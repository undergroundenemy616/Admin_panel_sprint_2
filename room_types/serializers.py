from rest_framework import serializers

from offices.models import Office
from room_types.models import RoomType


class RoomTypeSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)
    title = serializers.CharField(max_length=140, required=False)

    class Meta:
        model = RoomType
        fields = '__all__'


class CreateRoomTypeSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)

    class Meta:
        model = RoomType
        exclude = ['pre_defined', ]


class ListCreateRoomType(serializers.ModelSerializer):
    pass


class UpdateRoomTypeSerializer(serializers.ModelSerializer):
    pass
