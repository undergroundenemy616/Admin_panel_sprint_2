from rest_framework import serializers
# TODO: from zones.models import Zone
from tables.models import Table
from rooms.models import Room
from floors.models import Floor
from offices.models import OfficeZone
from files.models import File
from tables.serializers import TableSerializer


class EditRoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    tables = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), many=True, required=False)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
    zone = serializers.PrimaryKeyRelatedField(queryset=OfficeZone.objects.all(), required=False)
    title = serializers.CharField(max_length=256, required=False)
    description = serializers.CharField(max_length=256, required=False)
    type = serializers.CharField(max_length=128, required=False)

    class Meta:
        model = Room
        fields = ['floor', 'tables', 'images', 'zone', 'title', 'description', 'type']


class CreateRoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=True)
    title = serializers.CharField(max_length=256, required=True)
    description = serializers.CharField(max_length=256, required=False)
    type = serializers.CharField(max_length=128, required=True)

    class Meta:
        model = Room
        fields = ['floor', 'title', 'description', 'type']


class FilterRoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=True)
    type = serializers.CharField(max_length=256, required=False)
    tags = serializers.ListField(required=False)
    start = serializers.IntegerField(min_value=1, required=False)
    limit = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = Room
        fields = ['floor', 'type', 'tags', 'start', 'limit']


class RoomSerializer(serializers.ModelSerializer):
    occupied = serializers.ReadOnlyField()
    capacity = serializers.ReadOnlyField()
    occupied_tables = serializers.ReadOnlyField()
    capacity_tables = serializers.ReadOnlyField()
    occupied_meeting = serializers.ReadOnlyField()
    capacity_meeting = serializers.ReadOnlyField()
    tables = TableSerializer(many=True)

    class Meta:
        model = Room
        fields = '__all__'
        depth = 3
