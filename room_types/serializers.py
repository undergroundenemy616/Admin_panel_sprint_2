from rest_framework import serializers

from offices.models import Office
from room_types.models import RoomType


class RoomTypeSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)

    class Meta:
        model = RoomType
        fields = '__all__'
