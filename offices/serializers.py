from datetime import datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from floors.models import Floor
from groups.models import Group
from licenses.models import License
from licenses.serializers import LicenseSerializer
from offices.models import Office, OfficeZone
from files.models import File
from floors.serializers import BaseFloorSerializer
from room_types.models import RoomType
from room_types.serializers import RoomTypeSerializer


class OfficeZoneSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OfficeZone
        fields = '__all__'
        depth = 1


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


class CreateOfficeSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(),
                                                required=False,  # todo optimaze field
                                                help_text='Images must contains primary keys.',
                                                many=True)
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(),
                                                 required=True,
                                                 write_only=True,
                                                 validators=[validate_license])
    working_hours = serializers.CharField(max_length=128,
                                          required=False,
                                          validators=[working_hours_validator],
                                          help_text='Working hours `%H:%M-%H:%M`.')

    floors = BaseFloorSerializer(many=True, read_only=True)
    zones = OfficeZoneSerializer(many=True, read_only=True)
    floors_number = serializers.ReadOnlyField(default=1)
    occupied = serializers.ReadOnlyField(default=0)
    capacity = serializers.ReadOnlyField(default=0)
    occupied_tables = serializers.ReadOnlyField(default=0)
    capacity_tables = serializers.ReadOnlyField(default=0)
    occupied_meeting = serializers.ReadOnlyField(default=0)
    capacity_meeting = serializers.ReadOnlyField(default=0)

    class Meta:
        model = Office
        fields = '__all__'
        depth = 3

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
        # response['data'] = instance.get_office_booking_data()
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
        RoomType.objects.create(office=office,
                                title='Рабочее место',
                                bookable=True,
                                work_interval_days=90,
                                pre_defined=True)
        RoomType.objects.create(office=office,
                                title='Переговорная',
                                bookable=True,
                                work_interval_hours=24,
                                unified=True,
                                pre_defined=True)
        office_zone = OfficeZone.objects.create(office=office, is_deletable=False)  # create zone
        groups = Group.objects.filter(is_deletable=False)
        if groups:
            office_zone.groups.add(*groups)  # add to group whitelist
        return office

    def update(self, instance, validated_data):
        """Updating existing office without license."""
        validated_data.pop('license', None)
        return super(CreateOfficeSerializer, self).update(instance, validated_data)

    # TODO:
    # slow performance of images validation. See more ManyRelatedField
