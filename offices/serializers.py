from datetime import datetime
from typing import Any, Dict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.models import File
from files.serializers import FileSerializer, image_serializer
from floors.models import Floor
from floors.serializers import FloorSerializer
from groups.models import Group
from groups.serializers import GroupSerializer
from licenses.models import License
from licenses.serializers import LicenseSerializer
from offices.models import Office, OfficeZone
from room_types.models import RoomType
from rooms.serializers import RoomMarkerSerializer
from tables.models import Table


class SwaggerOfficeParametrs(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    search = serializers.CharField(required=False, max_length=256)
    type = serializers.CharField(required=False, max_length=256)


class SwaggerZonesParametrs(serializers.Serializer):
    id = serializers.UUIDField()


def office_base_serializer(office: Office) -> Dict[str, Any]:
    license = {
        'id': str(office.license.id),
        'forever': office.license.forever,
        'issued_at': str(office.license.issued_at),
        'tables_infinite': office.license.tables_infinite
    }
    if not office.license.forever:
        license['expires_at'] = str(office.license.expires_at)
        # if datetime.strptime(office.license.expires_at, '%Y-%m-%d') > datetime.now():
        if office.license.expires_at > datetime.now():
            license['expiry_status'] = "OK"
        else:
            license['expiry_status'] = "expired"
    if not office.license.tables_infinite:
        license['tables_available'] = int(office.license.tables_available)
        license['tables_remain'] = int(office.license.tables_available) - int(office.floors.tables.all().count())
        license['tables_status'] = "OK"  # TODO разобраться в логике этого поля
    tables = Table.objects.filter(room__floor__office_id=office.id).select_related('room__floor__office_id')
    capacity = tables.count()
    occupied = tables.filter(is_occupied=True).count()
    capacity_meeting = tables.filter(room__type__unified=True).count()
    occupied_meeting = tables.filter(room__type__unified=True, is_occupied=True).count()
    capacity_tables = tables.filter(room__type__unified=False).count()
    occupied_tables = tables.filter(room__type__unified=False, is_occupied=True).count()
    return {
        'id': str(office.id),
        'title': office.title,
        'description': office.description,
        'working_hours': office.working_hours,
        'service_email': office.service_email,
        'floors_number': office.floors.count(),
        'occupied': occupied,
        'capacity': capacity,
        'occupied_tables': occupied_tables,
        'capacity_tables': capacity_tables,
        'occupied_meeting': occupied_meeting,
        'capacity_meeting': capacity_meeting,
        'floors': [office_floor_serializer(floor=floor) for floor in office.floors.all()],
        'images': [image_serializer(image=image) for image in office.images.all()],
        'license': license
    }


def office_floor_serializer(floor: Floor) -> Dict[str, Any]:
    return {
        'id': str(floor.id),
        'title': floor.title
    }


class BaseOfficeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeZone
        fields = '__all__'
        depth = 1


class OfficeZoneSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OfficeZone
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        response = dict()
        response['id'] = instance.id
        response['title'] = instance.title
        response['pre_defined'] = not instance.is_deletable
        response['office'] = {
            'id': instance.office.id,
            'title': instance.office.title
        }
        if instance.groups:
            response['groups'] = [GroupSerializer(instance=group).data for group in instance.groups.all()]
        else:
            response['groups'] = []
        return response


class CreateUpdateOfficeZoneSerializer(serializers.ModelSerializer):
    title = serializers.ListField(child=serializers.CharField(max_length=140), required=True)
    group_whitelist_visit = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Group.objects.all()), required=False)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)

    class Meta:
        model = OfficeZone
        fields = ['title', 'group_whitelist_visit', 'office']

    def to_representation(self, instance):
        response = dict()
        if isinstance(instance, list):
            result = []
            for zone in instance:
                result.append(OfficeZoneSerializer(zone).data)
            return result
        response['id'] = instance.id
        response['title'] = instance.title
        response['pre_defined'] = not instance.is_deletable
        response['office'] = {
            'id': instance.office.id,
            'title': instance.office.title
        }
        response['groups'] = [GroupSerializer(instance=group).data for group in instance.groups.all()]
        return response

    def create(self, validated_data):
        titles = validated_data.pop('title')
        office = validated_data.pop('office')
        group_whitelist = validated_data.pop('group_whitelist_visit')
        all_existing_groups = Group.objects.all()
        groups_id = [group.id for group in all_existing_groups]
        if len(titles) > 1:
            zones_to_create = []
            for title in titles:
                zone_exist = OfficeZone.objects.filter(title=title, office=office)
                if zone_exist:
                    continue
                zones_to_create.append(OfficeZone(title=title, office=office))
            if group_whitelist and len(group_whitelist) > 0:
                for group in group_whitelist:
                    if group.id in groups_id:
                        for zone in zones_to_create:
                            zone.groups.add(group)
                    else:
                        continue
            OfficeZone.objects.bulk_create(zones_to_create)
            return zones_to_create
        zone_exist = OfficeZone.objects.filter(title=titles[0], office=office)
        if zone_exist:
            raise serializers.ValidationError('Zone already exist')
        new_zone = OfficeZone.objects.create(title=titles[0], office=office)
        if group_whitelist:
            for group in group_whitelist:
                if group.id in groups_id:
                    new_zone.groups.add(group)
                else:
                    continue
        return new_zone

    def update(self, instance, validated_data):
        title = validated_data.pop('title')
        validated_data['title'] = title[0]
        groups = validated_data.pop('group_whitelist_visit')
        validated_data['groups'] = groups
        return super(CreateUpdateOfficeZoneSerializer, self).update(instance,validated_data)


def working_hours_validator(value: str) -> str:
    """Validate working hours of current office.

    Every office must have start hours and end hours.
    Start hours (start time) can not be greater than end hours.

    Args:
        value: start and end time, format `%H:%M-%H:%M`, eg. `07:00-21:00`
    Returns:
        validated start and end time (string type)
    Raises:
        ValidationError
    """
    try:
        times = value.split('-')
        start_time = datetime.strptime(times[0], '%H:%M')
        end_time = datetime.strptime(times[1], '%H:%M')
    except (KeyError, AttributeError, IndexError, ValueError):
        msg = 'Invalid time row.'
        raise ValidationError(msg)

    if not start_time < end_time:
        msg = 'Start time can not be less or equal than end time.'
        raise ValidationError(msg)
    return value


def validate_license(value: License) -> License:
    """Check usages of current license.

    If license already in used by any office - raise ValidationError.

    Args:
        value: License object
    Returns:
        License object
    Raises:
        ValidationError: License is already in used
    """
    is_used = Office.objects.filter(license=value).exists()
    if is_used:
        raise ValidationError('License is already in used.')
    return value


class OfficeSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(),
                                                required=False,  # todo optimaze field
                                                help_text='Images must contains primary keys.',
                                                many=True)
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(),
                                                 required=True,
                                                 write_only=True)  # validators=[validate_license]
    working_hours = serializers.CharField(max_length=128,
                                          required=False,
                                          validators=[working_hours_validator],
                                          help_text='Working hours `%H:%M-%H:%M`.')

    class Meta:
        model = Office
        fields = '__all__'
        depth = 3

    def to_representation(self, instance):
        response = super(OfficeSerializer, self).to_representation(instance)
        response['images'] = [FileSerializer(instance=image).data for image in instance.images.all()]
        return response


class CreateOfficeSerializer(OfficeSerializer):
    floors = FloorSerializer(many=True, read_only=True)
    zones = OfficeZoneSerializer(many=True, read_only=True)

    # fields are default, cuz there are no need to calculate them
    floors_number = serializers.ReadOnlyField(default=1)
    occupied = serializers.ReadOnlyField(default=0)
    capacity = serializers.ReadOnlyField(default=0)
    occupied_tables = serializers.ReadOnlyField(default=0)
    capacity_tables = serializers.ReadOnlyField(default=0)
    occupied_meeting = serializers.ReadOnlyField(default=0)
    capacity_meeting = serializers.ReadOnlyField(default=0)

    def to_representation(self, instance):
        """Basic `.to_representation()` with license.

        Frontend required license as nested object, not primary key.
        Bad practice...

        Args:
            instance: current office instance
        Returns:
            dict as response data
        """
        response = super().to_representation(instance)
        response['license'] = LicenseSerializer(instance.license).data
        return response

    def create(self, validated_data):
        """Create office with default data.

        When we create any office, we must also create `floor`,
            `office_zone`, `groups`. For many information check out necessary serializers.
        There are some issues, ex. when we validation ManyRelatedField like license,
            in this case all license will be validate one by one instead of all

        Args:
            validated_data: data after calling `.is_valid()`.
        Returns:
            instance of office
        """
        office = super(CreateOfficeSerializer, self).create(validated_data)
        Floor.objects.create(office=office, title='Default floor.')  # create floor
        room_types = [RoomType(office=office,
                               title='Рабочее место',
                               bookable=True,
                               work_interval_days=90,
                               is_deletable=False),
                      RoomType(office=office,
                               title='Переговорная',
                               bookable=True,
                               work_interval_hours=24,
                               unified=True,
                               is_deletable=False)]  # Create of two default room_type to office
        RoomType.objects.bulk_create(room_types)
        office_zone = OfficeZone.objects.create(office=office, is_deletable=False)  # create zone
        groups = Group.objects.filter(is_deletable=False)
        if groups:
            office_zone.groups.add(*groups)  # add to group whitelist
        return office

    def update(self, instance, validated_data):
        """Updating existing office without license."""
        validated_data.pop('license', None)
        return super(CreateOfficeSerializer, self).update(instance, validated_data)


class ListOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'
        depth = 2

    def to_representation(self, instance):
        response = super(ListOfficeSerializer, self).to_representation(instance)
        response['floors'] = [{'id': FloorSerializer(instance=floor).data['id'],
                               'title': FloorSerializer(instance=floor).data['title']}
                              for floor in instance.floors.all()]
        response['floors_number'] = instance.floors.count()
        response['capacity'] = Table.objects.filter(room__floor__office_id=instance.id).count()
        response['occupied'] = Table.objects.filter(room__floor__office_id=instance.id, is_occupied=True).count()
        response['capacity_meeting'] = Table.objects.filter(
            room__type__unified=True,
            room__floor__office_id=instance.id
        ).count()
        response['occupied_meeting'] = Table.objects.filter(
            room__type__unified=True,
            room__floor__office_id=instance.id,
            is_occupied=True
        ).count()
        response['capacity_tables'] = Table.objects.filter(room__floor__office_id=instance.id).count()
        response['occupied_tables'] = Table.objects.filter(room__floor__office_id=instance.id, is_occupied=True).count()
        response['license'] = LicenseSerializer(instance=instance.license).data
        response['zones'] = [BaseOfficeZoneSerializer(instance=zone).data for zone in instance.zones.all()]
        return response


# TODO Get this out when front comes
class OptimizeListOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        response = super(OptimizeListOfficeSerializer, self).to_representation(instance)
        # response['floors'] = [{'id': FloorSerializer(instance=floor).data['id'],
        #                        'title': FloorSerializer(instance=floor).data['title']}
        #                       for floor in instance.floors.all()]
        response['floors_number'] = instance.floors.count()
        response['capacity'] = Table.objects.filter(room__floor__office_id=instance.id).count()
        response['occupied'] = Table.objects.filter(room__floor__office_id=instance.id, is_occupied=True).count()
        response['capacity_meeting'] = Table.objects.filter(
            room__type__unified=True,
            room__floor__office_id=instance.id
        ).count()
        response['occupied_meeting'] = Table.objects.filter(
            room__type__unified=True,
            room__floor__office_id=instance.id,
            is_occupied=True
        ).count()
        response['capacity_tables'] = Table.objects.filter(room__floor__office_id=instance.id).count()
        response['occupied_tables'] = Table.objects.filter(room__floor__office_id=instance.id, is_occupied=True).count()
        response['license'] = LicenseSerializer(instance=instance.license).data
        # response['zones'] = [BaseOfficeZoneSerializer(instance=zone).data for zone in instance.zones.all()]
        return response
