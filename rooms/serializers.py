from rest_framework import serializers
# TODO: from zones.models import Zone
from rest_framework.exceptions import ValidationError

from files.serializers import FileSerializer
from offices.models import Office
from room_types.models import RoomType
from room_types.serializers import RoomTypeSerializer
from rooms.models import Room, RoomMarker
from floors.models import Floor
from files.models import File
from tables.serializers import TableSerializer


class BaseRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'
        depth = 1


class RoomSerializer(serializers.ModelSerializer):
    tables = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)

    class Meta:
        model = Room
        fields = ['tables', 'images', 'type']

    def to_representation(self, instance):
        response = BaseRoomSerializer(instance=instance).data
        room_type = response.pop('type')
        response['type'] = room_type['title']
        response['tables'] = [TableSerializer(instance=table).data for table in instance.tables.all()]
        response['capacity'] = instance.tables.count()
        response['marker'] = instance.room_marker if hasattr(instance, 'room_marker') else None
        return response


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
    type = serializers.CharField(required=True)
    seats_amount = serializers.IntegerField(required=False, default=0)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, many=True)

    class Meta:
        model = Room
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        instance: Room
        data = super(CreateRoomSerializer, self).to_representation(instance)
        data['capacity'] = instance.tables.count()
        data['occupied'] = 0
        data['images'] = FileSerializer(instance=instance.images, many=True).data
        data['type'] = RoomTypeSerializer(instance=instance.type).data

        return data

    def create(self, validated_data):
        room_type = RoomType.objects.filter(title=validated_data['type'],
                                            office_id=validated_data['floor'].office.id).first()
        if not room_type:
            raise ValidationError(f'RoomType {room_type} does not exists.')
        validated_data['type'] = room_type
        instance = self.Meta.model.objects.create(**validated_data)
        return instance


class UpdateRoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    type = serializers.CharField(required=False)
    seats_amount = serializers.IntegerField(required=False, default=0)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False)

    class Meta:
        model = Room
        fields = ['title', 'description', 'images', 'floor', 'type', 'seats_amount']
        depth = 1

    def to_representation(self, instance):
        instance: Room
        data = super(UpdateRoomSerializer, self).to_representation(instance)
        data['capacity'] = instance.tables.count()
        data['occupied'] = 0
        data['images'] = FileSerializer(instance=instance.images, many=True).data
        data['type'] = RoomTypeSerializer(instance=instance.type).data

        return data

    def update(self, instance, validated_data):
        if validated_data.get('type'):
            room_type = RoomType.objects.filter(title=validated_data['type'],
                                                office_id=validated_data['floor'].office.id).first()
            if not room_type:
                raise ValidationError(f'RoomType {room_type} does not exists.')
            validated_data['type'] = room_type
        return super(UpdateRoomSerializer, self).update(instance, validated_data)


class FilterRoomSerializer(serializers.ModelSerializer):
    """Only for filtering given query string."""
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    type = serializers.CharField(max_length=256, required=False)  # Todo fields will be deleted
    tags = serializers.ListField(required=False)

    class Meta:
        model = Room
        fields = ['floor', 'type', 'tags', 'office']
