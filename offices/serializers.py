from datetime import datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from offices.models import Office, OfficeZone
from files.models import File
from licenses.models import License
from floors.serializers import FloorSerializer


def working_hours_validator(value):
    try:
        times = value.split('-')
        start_time = datetime.strptime(times[0], '%H:%M')
        end_time = datetime.strptime(times[1], '%H:%M')
    except Exception as err:
        print(str(err))
        raise ValidationError

    if not start_time < end_time:
        msg = 'Start time can not be less or equal than end time'
        raise ValidationError(msg)
    return value


class OfficeSerializer(serializers.ModelSerializer):
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(),
                                                 required=True,
                                                 write_only=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(),
                                                many=True,
                                                required=False,
                                                write_only=True,  # todo change field
                                                help_text='Images must contains primary keys.')
    working_hours = serializers.CharField(max_length=128,
                                          required=False,
                                          validators=[working_hours_validator],
                                          help_text='Working hours `%H:%M-%H:%M`.')

    class Meta:
        model = Office
        fields = '__all__'

    # def create(self, validated_data):
    #     images = validated_data.pop('images', None)
    #     instance = Office.objects.create(**validated_data)  # create office
    #     if images
    #
    #     return instance

    def update(self, instance, validated_data):
        validated_data.pop('license', None)
        return super(OfficeSerializer, self).update(instance, validated_data)


class ListOfficeSerializer(serializers.ModelSerializer):
    # license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(), required=True, write_only=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(),
                                                many=True,
                                                required=False,
                                                write_only=True,
                                                help_text='Images must contains primary keys.')
    floors = FloorSerializer(many=True, read_only=True)
    working_hours = serializers.CharField(max_length=128,
                                          required=False,
                                          validators=[working_hours_validator],
                                          help_text='Working hours `%H:%M-%H:%M`.')

    class Meta:
        model = Office
        fields = '__all__'
        depth = 1


class OfficeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeZone
        fields = '__all__'
        depth = 1
