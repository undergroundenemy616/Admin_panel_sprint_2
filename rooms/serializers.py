from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.models import File
from files.serializers import FileSerializer
from floors.models import Floor
from offices.models import Office, OfficeZone
from room_types.models import RoomType
from room_types.serializers import RoomTypeSerializer
from rooms.models import Room, RoomMarker
from tables.models import Table
from tables.serializers import TableSerializer


class SwaggerRoomParameters(serializers.Serializer):
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    range_from = serializers.IntegerField(required=False)
    range_to = serializers.IntegerField(required=False)
    marker = serializers.IntegerField(required=False)
    image = serializers.IntegerField(required=False)
    zone = serializers.UUIDField(required=False)
    floor = serializers.UUIDField(required=False)
    office = serializers.UUIDField(required=False)
    type = serializers.CharField(required=False)
    tags = serializers.ListField(required=False)


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
        response['room_type_color'] = room_type['color']
        response['room_type_unified'] = room_type['unified']
        response['is_bookable'] = room_type['bookable']
        response['room_type_icon'] = room_type['icon']   #[FileSerializer(instance=room_type['icon']).data]
        response['tables'] = [TableSerializer(instance=table).data for table in instance.tables.all()]
        response['capacity'] = instance.tables.count()
        response['marker'] = RoomMarkerSerializer(instance=instance.room_marker).data if \
            hasattr(instance, 'room_marker') else None
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
    description = serializers.CharField(max_length=280, allow_blank=True)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=True)
    title = serializers.CharField(max_length=140)
    zone = serializers.PrimaryKeyRelatedField(queryset=OfficeZone.objects.all(), required=True)
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, many=True)

    class Meta:
        model = Room
        fields = ['description', 'floor', 'title', 'zone', 'type', 'images']
        depth = 1

    def to_representation(self, instance):
        instance: Room
        data = super(CreateRoomSerializer, self).to_representation(instance)
        data['id'] = instance.id
        from floors.serializers import FloorSerializer
        from offices.serializers import \
            OfficeZoneSerializer  # If not like this Import Error calls
        data['seats_amount'] = instance.seats_amount
        data['marker'] = None
        tables_nested = Table.objects.filter(room=instance.id)
        data['tables'] = [TableSerializer(instance=table).data for table in tables_nested]
        data['floor'] = FloorSerializer(instance=instance.floor).data
        data['zone'] = OfficeZoneSerializer(instance=instance.zone).data
        data['capacity'] = instance.tables.count()
        data['occupied'] = 0
        data['images'] = FileSerializer(instance=instance.images, many=True).data
        data['type'] = RoomTypeSerializer(instance=instance.type).data

        return data

    def create(self, validated_data):
        # room_type = RoomType.objects.filter(title=validated_data['type'],
        #                                     office_id=validated_data['floor'].office.id).first()
        # if not room_type:
        #     raise ValidationError(f'RoomType {room_type} does not exists.')
        # validated_data['type'] = room_type
        images = validated_data.pop('images')
        instance = self.Meta.model.objects.create(**validated_data)
        if len(images) != 0:
            for image in images:
                instance.images.add(image)
        return instance


class UpdateRoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)
    # seats_amount = serializers.IntegerField(required=False, default=0)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, many=True, allow_empty=True)

    class Meta:
        model = Room
        fields = ['title', 'description', 'images', 'floor', 'type', 'seats_amount']
        depth = 1

    def to_representation(self, instance):
        instance: Room
        data = super(UpdateRoomSerializer, self).to_representation(instance)
        data['id'] = instance.id
        from floors.serializers import FloorSerializer
        from offices.serializers import \
            OfficeZoneSerializer  # If not like this Import Error calls
        data['seats_amount'] = instance.seats_amount
        data['marker'] = None
        tables_nested = Table.objects.filter(room=instance.id)
        data['tables'] = [TableSerializer(instance=table).data for table in tables_nested]
        data['floor'] = FloorSerializer(instance=instance.floor).data
        data['zone'] = OfficeZoneSerializer(instance=instance.zone).data
        data['capacity'] = instance.tables.count()
        data['occupied'] = 0
        data['images'] = FileSerializer(instance=instance.images, many=True).data
        data['type'] = instance.type.title

        return data

    # def update(self, instance, validated_data):
    #     if validated_data.get('type'):
    #         room_type = RoomType.objects.filter(title=validated_data['type'],
    #                                             office_id=validated_data['floor'].office.id).first()
    #         if not room_type:
    #             raise ValidationError(f'RoomType {room_type} does not exists.')
    #         validated_data['type'] = room_type
    #     return super(UpdateRoomSerializer, self).update(instance, validated_data)


class FilterRoomSerializer(serializers.ModelSerializer):
    """Only for filtering given query string."""
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), many=True, required=False)
    type = serializers.CharField(max_length=256, required=False)  # Todo fields will be deleted
    tags = serializers.ListField(required=False)
    search = serializers.CharField(required=False)
    zone = serializers.PrimaryKeyRelatedField(queryset=OfficeZone.objects.all(), many=True, required=False)

    class Meta:
        model = Room
        fields = ['floor', 'type', 'tags', 'office', 'search', 'zone']


class RoomMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMarker
        fields = '__all__'
