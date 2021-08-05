from datetime import datetime

from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta

from files.models import File
from floors.models import Floor
from groups.models import Group
from groups.serializers_admin import AdminGroupForOfficeSerializer
from licenses.models import License
from offices.models import Office, OfficeZone
from room_types.models import RoomType


# Other functions
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


class AdminOfficeZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = OfficeZone
        fields = ['id', 'title', 'office']

    def to_representation(self, instance):
        response = super(AdminOfficeZoneSerializer, self).to_representation(instance)
        response['pre_defined'] = not instance.is_deletable
        response['groups'] = AdminGroupForOfficeSerializer(instance=instance.groups.all(), many=True).data
        return response


class AdminOfficeZoneCreateSerializer(serializers.ModelSerializer):
    titles = serializers.ListField(child=serializers.CharField())
    group_whitelist_visit = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, required=False)

    class Meta:
        model = OfficeZone
        fields = ['titles', 'office', 'group_whitelist_visit']

    @atomic()
    def create(self, validated_data):
        office_zones_to_create = []

        for title in validated_data.get('titles'):
            if OfficeZone.objects.filter(title=title, office=validated_data['office']).exists():
                raise ValidationError(detail={"message": "OfficeZone already exists"}, code=400)

        if validated_data.get('group_whitelist_visit'):
            for title in set(validated_data['titles']):
                zone = OfficeZone(title=title, office=validated_data.get('office'))
                for group in validated_data['group_whitelist_visit']:
                    zone.groups.add(group)
                office_zones_to_create.append(zone)
        else:
            for title in set(validated_data['titles']):
                office_zones_to_create.append(OfficeZone(title=title, office=validated_data.get('office')))

        office_zones = OfficeZone.objects.bulk_create(office_zones_to_create)
        return office_zones

    def to_representation(self, instance):
        response = dict()
        if isinstance(instance, OfficeZone):
            response['result'] = AdminOfficeZoneSerializer(instance=instance).data
        else:
            response['result'] = AdminOfficeZoneSerializer(instance=instance, many=True).data
        return response


class AdminOfficeZoneUpdateSerializer(serializers.ModelSerializer):
    group_whitelist_visit = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), required=False,
                                                               many=True, source='groups')

    class Meta:
        model = OfficeZone
        exclude = ['is_deletable', 'groups']

    def to_representation(self, instance):
        return AdminOfficeZoneSerializer(instance=instance).data


class AdminFloorForOffice(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'title']


class AdminGroupsForOffice(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title']

    def to_representation(self, instance):
        response = super(AdminGroupsForOffice, self).to_representation(instance)
        response['count'] = instance.accounts.count()
        return response


class AdminZoneForOffice(serializers.ModelSerializer):
    groups = AdminGroupsForOffice(many=True, required=False)

    class Meta:
        model = OfficeZone
        fields = ['id', 'title', 'groups']

    def to_representation(self, instance):
        response = super(AdminZoneForOffice, self).to_representation(instance)
        response['pre_defined'] = not instance.is_deletable
        return response


class AdminRoomTypeForOffice(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        exclude = ['is_deletable']

    def to_representation(self, instance):
        response = super(AdminRoomTypeForOffice, self).to_representation(instance)
        response['pre_defined'] = not instance.is_deletable
        return response


class AdminFileForOffice(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'


class AdminLicenseForOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = '__all__'


class AdminOfficeCreateSerializer(serializers.ModelSerializer):
    floors = AdminFloorForOffice(many=True, required=False)
    zones = AdminZoneForOffice(many=True, required=False)
    room_types = AdminRoomTypeForOffice(many=True, source='roomtypes', required=False)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all())
    working_hours = serializers.CharField(max_length=128,
                                          required=False,
                                          validators=[working_hours_validator],
                                          help_text='Working hours `%H:%M-%H:%M`.')

    class Meta:
        model = Office
        fields = '__all__'

    def validate(self, attrs):
        if Office.objects.filter(license=attrs['license']).exclude(
                pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError(detail='Office with this license is already exists', code=400)
        return attrs

    @atomic()
    def create(self, validated_data):
        instance = super(AdminOfficeCreateSerializer, self).create(validated_data)
        Floor.objects.create(office=instance, title='Default floor.')  # create floor
        if self.context.get('Language') != 'ru':
            room_types = [RoomType(office=instance,
                                   title='Workplace',
                                   bookable=True,
                                   work_interval_days=90,
                                   is_deletable=False),
                          RoomType(office=instance,
                                   title='Meeting',
                                   bookable=True,
                                   work_interval_hours=24,
                                   unified=True,
                                   is_deletable=False)]  # Create of two default room_type to office
        else:
            room_types = [RoomType(office=instance,
                                   title='Рабочее место',
                                   bookable=True,
                                   work_interval_days=90,
                                   is_deletable=False),
                          RoomType(office=instance,
                                   title='Переговорная',
                                   bookable=True,
                                   work_interval_hours=24,
                                   unified=True,
                                   is_deletable=False)]  # Create of two default room_type to office
        RoomType.objects.bulk_create(room_types)
        if self.context.headers.get('Language') != 'ru':
            office_zone = OfficeZone.objects.create(office=instance, is_deletable=False, title='Coworking zone')  # create zone
        else:
            office_zone = OfficeZone.objects.create(office=instance, is_deletable=False)  # create zone
        groups = Group.objects.filter(is_deletable=False)
        if groups:
            office_zone.groups.add(*groups)  # add to group whitelist
        return instance

    def to_representation(self, instance):
        response = super(AdminOfficeCreateSerializer, self).to_representation(instance)
        response['images'] = AdminFileForOffice(instance.images, many=True).data
        response['license'] = AdminLicenseForOfficeSerializer(instance.license).data
        return response


class AdminOfficeSerializer(serializers.ModelSerializer):
    working_hours = serializers.CharField(max_length=128,
                                          required=False,
                                          validators=[working_hours_validator],
                                          help_text='Working hours `%H:%M-%H:%M`.')

    class Meta:
        model = Office
        exclude = ['images']

    def to_representation(self, instance):
        response = super(AdminOfficeSerializer, self).to_representation(instance)
        response['license'] = AdminLicenseForOfficeSerializer(instance.license).data
        response['floors_number'] = instance.floors.count()
        response['capacity'] = instance.capacity
        response['occupied'] = instance.occupied
        response['capacity_meeting'] = instance.capacity_meeting
        response['occupied_meeting'] = instance.occupied_meeting
        response['capacity_tables'] = instance.capacity_tables
        response['occupied_tables'] = instance.occupied_tables
        return response


class AdminOfficeSingleSerializer(AdminOfficeSerializer):
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True)

    class Meta:
        model = Office
        fields = '__all__'

    def to_representation(self, instance):
        response = super(AdminOfficeSingleSerializer, self).to_representation(instance)
        response['images'] = AdminFileForOffice(instance=instance.images, many=True).data
        return response

    @atomic()
    def update(self, instance, validated_data):
        for image in instance.images.all():
            if str(image.id) not in validated_data.get('images'):
                image.delete()

        return super(AdminOfficeSingleSerializer, self).update(instance=instance, validated_data=validated_data)
