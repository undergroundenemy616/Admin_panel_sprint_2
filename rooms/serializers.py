from rest_framework import serializers
# TODO: from zones.models import Zone
from tables.models import Table
from rooms.models import Room
from floors.models import Floor
from files.models import File
from tables.serializers import TableSerializer


class EditRoomSerializer(serializers.ModelSerializer):
    tables = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), many=True, required=False)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
    title = serializers.CharField(max_length=256, required=False)
    description = serializers.CharField(max_length=256, required=False)
    type = serializers.CharField(max_length=128, required=False)  # Todo fields will be deleted

    # zone = serializers.PrimaryKeyRelatedField(queryset=OfficeZone.objects.all(), required=False)
    # floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)

    class Meta:
        model = Room
        fields = ['tables', 'images', 'title', 'description', 'type']  # , 'zone', 'floor',


class RoomSerializer(serializers.ModelSerializer):
    tables = TableSerializer(many=True, read_only=True)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())

    occupied = serializers.ReadOnlyField()
    capacity = serializers.ReadOnlyField()
    occupied_tables = serializers.ReadOnlyField()
    capacity_tables = serializers.ReadOnlyField()
    occupied_meeting = serializers.ReadOnlyField()
    capacity_meeting = serializers.ReadOnlyField()

    class Meta:
        model = Room
        fields = '__all__'
        depth = 1
        read_only_fields = ('occupied',
                            'capacity',
                            'occupied_tables',
                            'capacity_tables',
                            'occupied_meeting',
                            'capacity_meeting',
                            'tables',
                            'floor')


class FilterRoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=True)
    type = serializers.CharField(max_length=256, required=False)  # Todo fields will be deleted
    tags = serializers.ListField(required=False)

    class Meta:
        model = Room
        fields = ['floor', 'type', 'tags']


# class RoomTypeSerializer(serializers.ModelSerializer):  # todo use it
#     room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=True)
#
#     class Meta:
#         model = RoomType
#         fields = '__all__'
