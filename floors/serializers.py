from rest_framework import serializers
from offices.models import Office
from floors.models import Floor
from rooms.serializers import RoomSerializer


class EditFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['title', ]


class FilterFloorSerializer(serializers.ModelSerializer):
    type = serializers.CharField(max_length=256, required=False)
    tags = serializers.ListField(required=False)
    start = serializers.IntegerField(min_value=1, required=False)
    limit = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = Floor
        fields = ['type', 'tags', 'start', 'limit']


class CreateFloorSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)

    class Meta:
        model = Floor
        fields = '__all__'


class FloorSerializer(serializers.ModelSerializer):
    occupied = serializers.ReadOnlyField()
    capacity = serializers.ReadOnlyField()
    occupied_tables = serializers.ReadOnlyField()
    capacity_tables = serializers.ReadOnlyField()
    occupied_meeting = serializers.ReadOnlyField()
    capacity_meeting = serializers.ReadOnlyField()
    rooms = RoomSerializer(many=True)

    class Meta:
        model = Floor
        fields = '__all__'
