from rest_framework import serializers
# TODO: from zones.models import Zone
from room_types.models import RoomType
from room_types.serializers import RoomTypeSerializer
from rooms.models import Room
from floors.models import Floor
from files.models import File
from tables.serializers import TableSerializer


class RoomSerializer(serializers.ModelSerializer):
    tables = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
    room_type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)

    class Meta:
        model = Room
        fields = '__all__'


class NestedRoomSerializer(RoomSerializer):
    tables = TableSerializer(many=True, read_only=True)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())

    # occupied = serializers.ReadOnlyField()
    # capacity = serializers.ReadOnlyField()
    # occupied_tables = serializers.ReadOnlyField()
    # capacity_tables = serializers.ReadOnlyField()
    # occupied_meeting = serializers.ReadOnlyField()
    # capacity_meeting = serializers.ReadOnlyField()

    class Meta:
        model = Room
        fields = '__all__'
        depth = 1


class CreateRoomSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False)

    class Meta:
        model = Room
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        instance: Room
        data = super(CreateRoomSerializer, self).to_representation(instance)
        data['capacity'] = instance.tables.count()
        data['occupied'] = 0
        data['room_type'] = RoomTypeSerializer(instance=instance.room_type).data

        return data

    def create(self, validated_data):
        pass


class FilterRoomSerializer(serializers.ModelSerializer):
    """Only for filtering given query string."""
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=True)
    type = serializers.CharField(max_length=256, required=False)  # Todo fields will be deleted
    tags = serializers.ListField(required=False)

    class Meta:
        model = Room
        fields = ['floor', 'type', 'tags']
