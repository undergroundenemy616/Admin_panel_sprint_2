from datetime import datetime

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.serializers import TestBaseFileSerializer
from licenses.models import License
from offices.models import Office


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


class MobileOfficeBaseSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source='description')
    images = TestBaseFileSerializer(many=True)

    class Meta:
        model = Office
        fields = ['id', 'title', 'address', 'images']

    def to_representation(self, instance):
        response = super(MobileOfficeBaseSerializer, self).to_representation(instance)
        response['image'] = response.get('images')[:1]
        response.pop('images')
        return response


class MobileOfficeSerializer(serializers.ModelSerializer):
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(),
                                                 required=True,
                                                 write_only=True)  # validators=[validate_license]
    working_hours = serializers.CharField(max_length=128,
                                          required=False,
                                          validators=[working_hours_validator],
                                          help_text='Working hours `%H:%M-%H:%M`.')
    images = TestBaseFileSerializer(required=False, many=True, allow_null=True)

    class Meta:
        model = Office
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        response = super(MobileOfficeSerializer, self).to_representation(instance)
        return response
