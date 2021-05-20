from datetime import datetime

from django.db.models import Case, Count, Q, When
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.models import File
from files.serializers import FileSerializer, TestBaseFileSerializer
from floors.serializers import FloorSerializer
from groups.serializers import GroupSerializer
from licenses.models import License
from licenses.serializers import LicenseSerializer
from offices.models import Office, OfficeZone
from offices.serializers import BaseOfficeZoneSerializer
from tables.models import Table


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


class MobileOfficeBaseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    images = TestBaseFileSerializer(many=True)

    def to_representation(self, instance):
        response = super(MobileOfficeBaseSerializer, self).to_representation(instance)
        response['address'] = response.pop('description')
        response['image'] = response.get('images')[:1]
        response.pop('images')
        return response


class MobileListOfficeSerializer(serializers.ModelSerializer):  # Will die soon
    class Meta:
        model = Office
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        response = super(MobileListOfficeSerializer, self).to_representation(instance)
        response['floors'] = [{'id': FloorSerializer(instance=floor).data['id'],
                               'title': FloorSerializer(instance=floor).data['title']}
                              for floor in instance.floors.all()]
        response['floors_number'] = instance.floors.count()
        tables = Table.objects.filter(room__floor__office_id=instance.id).aggregate(
            occupied=Count(Case(When(is_occupied=True, then=1))),
            capacity=Count('*'),
            capacity_meeting=Count(Case(When(room__type__unified=True, then=1))),
            occupied_meeting=Count(Case(When(Q(is_occupied=True) & Q(room__type__unified=True), then=1))),
            capacity_tables=Count(Case(When(room__type__unified=False, then=1))),
            occupied_tables=Count(Case(When(Q(is_occupied=True) & Q(room__type__unified=False), then=1)))
        )
        response['capacity'] = tables['capacity']
        response['occupied'] = tables['occupied']
        response['capacity_meeting'] = tables['capacity_meeting']
        response['occupied_meeting'] = tables['occupied_meeting']
        response['capacity_tables'] = tables['capacity_tables']
        response['occupied_tables'] = tables['occupied_tables']
        response['license'] = LicenseSerializer(instance=instance.license).data
        response['zones'] = BaseOfficeZoneSerializer(instance=instance.zones.all(), many=True).data
        return response


class MobileOfficeSerializer(serializers.ModelSerializer):
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
        depth = 1

    def to_representation(self, instance):
        response = super(MobileOfficeSerializer, self).to_representation(instance)
        response['images'] = [FileSerializer(instance=image).data for image in instance.images.all()]
        return response


class MobileOfficeZoneSerializer(serializers.ModelSerializer):
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


def floor_serializer_for_office(floor):
    return {'id': floor.id,
            'title': floor.title}


def zone_serializer_for_office(zone):
    return {'id': zone.id,
            'title': zone.title}
