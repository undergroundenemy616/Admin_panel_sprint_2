from rest_framework import serializers
from rooms.models import Room
from room_types.models import RoomType


class RoomTypeSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=True)

    class Meta:
        model = RoomType
        fields = '__all__'
