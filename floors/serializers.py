from rest_framework import serializers
from files.models import File
from files.serializers import FileSerializer
from floors.models import Floor, FloorMap
from offices.models import Office
from room_types.models import RoomType
from rooms.serializers import RoomSerializer
from tables.models import Table


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


class FloorSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Floor
        fields = '__all__'
        depth = 1


class DetailFloorSerializer(FloorSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all())

    def to_representation(self, instance):
        data = super(DetailFloorSerializer, self).to_representation(instance)
        data['occupied'] = Table.objects.filter(room__floor_id=instance.id, is_occupied=True).count()
        data['capacity'] = Table.objects.filter(room__floor_id=instance.id).count()
        data['capacity_meeting'] = Table.objects.filter(room__type__unified=True, room__floor_id=instance.id).count()
        data['occupied_meeting'] = Table.objects.filter(
            room__type__unified=True,
            room__floor_id=instance.id,
            is_occupied=True
        ).count()
        data['capacity_tables'] = Table.objects.filter(room__floor_id=instance.id).count()
        data['occupied_tables'] = Table.objects.filter(room__floor_id=instance.id, is_occupied=True).count()


class NestedFloorSerializer(FloorSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all())


class FloorMapSerializer(serializers.ModelSerializer):
    image = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=True)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=True)

    class Meta:
        model = FloorMap
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        data = super(FloorMapSerializer, self).to_representation(instance)
        data['image'] = FileSerializer(instance=instance.image).data
        data['floor'] = FloorSerializer(instance=instance.floor).data
        return data
