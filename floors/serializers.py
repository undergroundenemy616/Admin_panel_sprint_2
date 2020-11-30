from rest_framework import serializers
from files.models import File
from files.serializers import FileSerializer
from floors.models import Floor, FloorMap
from offices.models import Office
from rooms.serializers import RoomSerializer
from tables.models import Table


class BaseFloorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Floor
        fields = '__all__'


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
    title = serializers.ListField(child=serializers.CharField(), required=True)

    class Meta:
        model = Floor
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        if not isinstance(instance, list):
            response = BaseFloorSerializer(instance=instance).data
            response['rooms'] = [RoomSerializer(instance=room).data for room in instance.rooms.all()]
            floor_map = FloorMap.objects.filter(floor=instance.id).first()
            if floor_map:
                response['floor_map'] = BaseFloorMapSerializer(instance=floor_map).data
            else:
                response['floor_map'] = None
            return response
        else:
            response = []
            for floor in instance:
                response.append(BaseFloorSerializer(instance=floor).data)
            return response

    def create(self, validated_data):
        titles = validated_data.pop('title')
        if len(titles) > 1:
            floor_to_create = []
            for title in titles:
                floor_to_create.append(Floor(title=title, office=validated_data['office']))
            instance = Floor.objects.bulk_create(floor_to_create)
            return instance
        else:
            validated_data['title'] = titles[0]
            return super(FloorSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        title = validated_data.pop('title')
        validated_data['title'] = title[0]
        return super(FloorSerializer, self).update(instance, validated_data)


class DetailFloorSerializer(FloorSerializer):
    rooms = RoomSerializer(many=True, read_only=True)

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
        return data


class EditFloorSerializer(DetailFloorSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)

    class Meta:
        model = Floor
        fields = '__all__'


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
        # data = super(FloorMapSerializer, self).to_representation(instance)
        # data['image'] = FileSerializer(instance=instance.image).data
        data = FloorSerializer(instance=instance.floor).data
        return data


class BaseFloorMapSerializer(serializers.ModelSerializer):

    class Meta:
        model = FloorMap
        fields = '__all__'
        depth = 1
