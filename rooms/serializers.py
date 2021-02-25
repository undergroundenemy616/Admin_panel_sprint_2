from typing import Any, Dict

from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.models import File
from files.serializers import FileSerializer, image_serializer, TestBaseFileSerializer
from floors.models import Floor
from groups.serializers import validate_csv_file_extension
from offices.models import Office, OfficeZone
from room_types.models import RoomType
from room_types.serializers import RoomTypeSerializer
from rooms.models import Room, RoomMarker
from tables.models import Rating, Table, TableTag, TableMarker
from tables.serializers import TableSerializer, table_tag_serializer, table_marker_serializer, TestTableSerializer


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


def base_serialize_room(room: Room) -> Dict[str, Any]:
    return {
        'id': str(room.id),
        'title': room.title,
        'description': room.description,
        'type': room.type.title,
        'zone': {
            'id': str(room.zone.id),
            'title': room.zone.title,
            'is_deletable': room.zone.is_deletable,
        } if room.zone else None,
        'floor': floor_serializer_for_room(floor=room.floor).copy(),
        'seats_amount': room.seats_amount,
        'room_type_color': room.type.color,
        'room_type_unified': room.type.unified,
        'is_occupied': False,
        'is_bookable': room.type.bookable,
        'room_type_icon': {
            'title': room.type.icon.title,
            'path': room.type.icon.path,
            'thumb': room.type.icon.thumb,
            'size': room.type.icon.size
        } if room.type.icon else None,
        'tables': TestTableSerializer(instance=room.tables.prefetch_related('tags', 'images').select_related('table_marker'), many=True).data,  # [table_serializer_for_room(table=table).copy() for table in
                   # room.tables.prefetch_related('tags', 'images').select_related('table_marker')],
        'capacity': room.tables.count(),
        'occupied': room.tables.filter(is_occupied=True).count(),
        'suitable_tables': room.tables.filter(is_occupied=False).count(),
        'marker': room_marker_serializer(marker=room.room_marker).copy() if hasattr(room, 'room_marker') else None,
        'images': [image_serializer(image=image).copy() for image in room.images.all()]
    }


def office_serializer(office: Office) -> Dict[str, Any]:
    return {
        'id': str(office.id),
        'title': office.title,
        'description': office.description,
        'working_hours': office.working_hours,
        'service_email': office.service_email,
        'license': str(office.license.id),
        'images': [image_serializer(image=image).copy() for image in office.images.all()]
    }


def floor_serializer_for_room(floor: Floor) -> Dict[str, Any]:
    return {
        'id': str(floor.id),
        'title': floor.title
    }


def table_serializer_for_room(table: Table) -> Dict[str, Any]:
    # tags = table.tags.all()
    # images = table.images.first()
    ratings = Rating.objects.raw(f"""select table_id as id, cast(sum(rating) as decimal)/count(rating) as table_rating, 
        count(rating) as number_of_votes
        from tables_rating
        where table_id = '{table.id}'
        group by table_id""")
    table_rating = 0
    table_ratings = 0
    for result in table_ratings:
        table_rating = result.table_rating
        table_ratings = result.number_of_votes
    return {
        'id': str(table.id),
        'title': table.title,
        'tags': [table_tag_serializer(tag=tag).copy() for tag in table.tags.all()],
        'images': list(image_serializer(image=table.images.first())) if table.images.first() else [],
        'rating': table_rating,
        # 'ratings': Rating.objects.filter(table_id=table.id).count(),
        'ratings': table_ratings,
        'description': table.description,
        'is_occupied': table.is_occupied,
        'room': str(table.room_id),
        'marker': table_marker_serializer(marker=table.table_marker).copy() if hasattr(table, 'table_marker') else None
    }


def room_marker_serializer(marker: RoomMarker) -> Dict[str, Any]:
    return {
        'icon': marker.icon if marker.icon else None,
        'x': float(marker.x),
        'y': float(marker.y),
    }


class TestRoomSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    type = serializers.PrimaryKeyRelatedField(read_only=True)
    zone = serializers.PrimaryKeyRelatedField(read_only=True)
    images = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    floor = serializers.PrimaryKeyRelatedField(read_only=True)
    seats_amount = serializers.IntegerField()

    def to_representation(self, instance):
        # response = BaseRoomSerializer(instance=instance).data
        response = super(TestRoomSerializer, self).to_representation(instance)
        # room_type = response.pop('type')
        response['type'] = instance.type.title if instance.type else None
        response['room_type_color'] = instance.type.color if instance.type else None
        response['room_type_unified'] = instance.type.unified if instance.type else None
        response['zone'] = {'id': instance.zone.id,
                            'title': instance.zone.title}
        response['floor'] = {'id': instance.floor.id,
                             'title': instance.floor.title}
        response['is_bookable'] = instance.type.bookable if instance.type else None
        response['room_type_icon'] = instance.type.icon if instance.type else None
        response['tables'] = TestTableSerializer(instance=instance.tables.prefetch_related('tags', 'images', 'tags__icon').select_related('table_marker'), many=True).data
        response['capacity'] = instance.tables.count()
        response['marker'] = TestRoomMarkerSerializer(instance=instance.room_marker).data if \
            hasattr(instance, 'room_marker') else None
        response['occupied'] = instance.tables.filter(is_occupied=True).count(),        # Take additional queries
        response['suitable_tables'] = instance.tables.filter(is_occupied=False).count() # Take additional queries
        return response


class RoomSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    tables = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    images = serializers.PrimaryKeyRelatedField(read_only=True, many=True, required=False)
    type = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    class Meta:
        model = Room
        fields = '__all__'  # ['tables', 'images', 'type']

    def to_representation(self, instance):
        # response = BaseRoomSerializer(instance=instance).data
        response = super(RoomSerializer, self).to_representation(instance)
        # room_type = response.pop('type')
        response['floor'] = {"id": instance.floor.id, "title": instance.floor.title}
        response['zone'] = {"id": instance.zone.id, "title": instance.zone.title}
        response['type'] = instance.type.title if instance.type else None
        response['room_type_color'] = instance.type.color if instance.type else None
        response['room_type_unified'] = instance.type.unified if instance.type else None
        response['is_bookable'] = instance.type.bookable if instance.type else None
        response['room_type_icon'] = instance.type.icon if instance.type else None
        response['tables'] = TestTableSerializer(instance=instance.tables.prefetch_related('tags', 'images').select_related('table_marker'), many=True).data
        response['capacity'] = instance.tables.count()
        response['marker'] = RoomMarkerSerializer(instance=instance.room_marker).data if \
            hasattr(instance, 'room_marker') else None
        response['occupied'] = instance.tables.filter(is_occupied=True).count(),
        response['suitable_tables'] = instance.tables.filter(is_occupied=False).count()
        return response


def table_tags_validator(tags):
    """Check is every tag in array exists. Delete when start using id"""
    if not tags:
        return True
    if len(tags[0].split(',')) > 1 and len(tags) == 1:
        tags = tags[0].split(',')

    for tag in tags:
        result = TableTag.objects.filter(title=tag).exists()
        if not result:
            raise ValidationError(f'Table_tag {tag} does not exists.')


def type_validatior(type):
    if not type:
        return True
    return RoomType.objects.filter(title=type).exists()


class RoomGetSerializer(serializers.Serializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    zone = serializers.PrimaryKeyRelatedField(queryset=OfficeZone.objects.all(), required=False)
    #type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)
    # TODO replace type_title with uuid
    type = serializers.CharField(validators=[type_validatior], required=False)
    date_to = serializers.DateTimeField(required=False)
    date_from = serializers.DateTimeField(required=False)
    tags = serializers.ListField(validators=[table_tags_validator], required=False)
    #tags = serializers.PrimaryKeyRelatedField(queryset=TableTag.objects.all(), required=False, many=True)
    # TODO replase tag title for tag id, need front fix, also fix in RoomsView


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
        data['tables'] = TableSerializer(instance=tables_nested, many=True).data
        data['floor'] = {'id': instance.floor.id,
                         'title': instance.floor.title
                         }  # FloorSerializer(instance=instance.floor).data
        data['zone'] = {'id': instance.zone.id,
                        'title': instance.zone.title
                        }  # OfficeZoneSerializer(instance=instance.zone).data
        data['capacity'] = instance.tables.count()
        data['occupied'] = 0
        data['images'] = FileSerializer(instance=instance.images, many=True).data
        data['type'] = RoomTypeSerializer(instance=instance.type).data
        data['room_type_color'] = instance.type.color
        data['room_type_unified'] = instance.type.unified
        data['is_bookable'] = instance.type.bookable
        data['is_occupied'] = False  # TODO: NEED to fix! In Flask: capacity == occupied

        return data

    def create(self, validated_data):
        # room_type = RoomType.objects.filter(title=validated_data['type'],
        #                                     office_id=validated_data['floor'].office.id).first()
        # if not room_type:
        #     raise ValidationError(f'RoomType {room_type} does not exists.')
        # validated_data['type'] = room_type
        images = validated_data.pop('images', [])
        instance = self.Meta.model.objects.create(**validated_data)
        if len(images) != 0:
            for image in images:
                instance.images.add(image)
        if instance.type.unified:
            Table.objects.create(title=f'Стол в {instance.title}', room_id=instance.id,)
        return instance


class UpdateRoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)
    # seats_amount = serializers.IntegerField(required=False, default=0)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, many=True, allow_empty=True)
    zone = serializers.PrimaryKeyRelatedField(queryset=OfficeZone.objects.all(), required=False)

    class Meta:
        model = Room
        fields = ['title', 'description', 'images', 'floor', 'type', 'seats_amount', 'zone']
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
        tables_nested = Table.objects.filter(room=instance.id).prefetch_related('tags', 'images').select_related('table_marker')
        data['tables'] = TestTableSerializer(instance=tables_nested, many=True).data
        data['floor'] = FloorSerializer(instance=instance.floor).data
        data['zone'] = OfficeZoneSerializer(instance=instance.zone).data
        data['capacity'] = instance.tables.count()
        data['occupied'] = 0
        data['images'] = TestBaseFileSerializer(instance=instance.images, many=True).data
        data['type'] = instance.type.title

        return data


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

    # def save(self, **kwargs):
    #     if self.validated_data['room'].type.unified:
    #         table_marker = TableMarker.objects.filter(table=self.validated_data['room'].tables.first()).first()
    #         if table_marker:
    #             table_marker.x = self.validated_data['x']
    #             table_marker.y = self.validated_data['y']
    #             table_marker.save()
    #         else:
    #             TableMarker.objects.create(table=self.validated_data['room'].tables.first(),
    #                                        x=self.validated_data['x'],
    #                                        y=self.validated_data['y'])
    #     return super(RoomMarkerSerializer, self).save()
    # TODO: For now it's don't need, but looks logic to do so. Need front fix for this.


class TestRoomMarkerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    room = serializers.PrimaryKeyRelatedField(read_only=True)
    icon = serializers.CharField()
    x = serializers.DecimalField(max_digits=4, decimal_places=2)
    y = serializers.DecimalField(max_digits=4, decimal_places=2)


class RoomSerializerCSV(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=True)

    class Meta:
        model = Room
        fields = ('floor', 'file')

    def create(self, validated_data):
        validate_csv_file_extension(file=validated_data['file'])

        file = validated_data.pop('file')
        floor = validated_data.pop('floor')
        rooms = []

        for chunk in list(file.read().splitlines()):
            room = []
            try:
                for item in chunk.decode('utf8').split(','):
                    room.append(item or None)
                if len(room) < 5:
                    room.extend([None]*(len(room)-5))
                rooms.append(room)
            except UnicodeDecodeError:
                for item in chunk.decode('cp1251').split(','):
                    room.append(item or None)
                if len(room) < 5:
                    room.extend([None]*(len(room)-5))
                rooms.append(room)

        rooms_to_create = []
        for room in rooms:
            rooms_to_create.append(Room(floor=floor, title=room[0], description=room[1],
                                        type=RoomType.objects.filter(title=room[2], office=floor.office).first(),
                                        zone=OfficeZone.objects.filter(title=room[3], office=floor.office).first(),
                                        seats_amount=room[4] or 1))
        try:
            Room.objects.bulk_create(rooms_to_create)
        except IntegrityError:
            raise ValidationError(detail={"detail": "Invalid CSV file format!"}, code=400)
        return ({
            "message": "OK",
            "result": RoomSerializer(instance=Room.objects.all(), many=True).data
        })

