from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from floors.models import Floor
from files.serializers_mobile import MobileBaseFileSerializer
from room_types.models import RoomType
from rooms.models import RoomMarker
from tables.models import TableMarker


# find min distance between two dots and return maximum available radius for point before intersection
def min_radius(markers: QuerySet, width: int, height: int) -> float:
    min_val = float(max(width, height))
    values = list(markers.values_list('x', 'y'))
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            current = ((float(values[i][0] / 100 * width - values[j][0] / 100 * width)) ** 2 +
                       float((values[i][1] / 100 * height - values[j][1] / 100 * height)) ** 2) ** 0.5
            if current < min_val:
                min_val = current
    return min_val / 2


class MobileFloorMapBaseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    height = serializers.IntegerField()
    width = serializers.IntegerField()
    image = MobileBaseFileSerializer()

    def to_representation(self, instance):
        response = super(MobileFloorMapBaseSerializer, self).to_representation(instance)
        return response


class MobileFloorMarkerParameters(serializers.Serializer):
    room_type = serializers.CharField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    tag = serializers.ListField(required=False)

    def validate(self, attrs):
        if attrs.get('room_type') and not RoomType.objects.filter(title=attrs.get('room_type')):
            raise ValidationError("RoomType not found", code=404)
        return attrs


class MobileFloorSuitableParameters(serializers.Serializer):
    office = serializers.UUIDField(required=False)
    room_type = serializers.CharField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    tag = serializers.ListField(required=False)


class MobileFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'title']


class MobileFloorMarkerSerializer(serializers.Serializer):
    room_markers_bookable = serializers.SerializerMethodField()
    room_markers_not_bookable = serializers.SerializerMethodField()
    table_markers = serializers.SerializerMethodField()
    max_room_marker_radius = serializers.SerializerMethodField()
    max_table_marker_radius = serializers.SerializerMethodField()

    def get_room_markers_bookable(self, obj):
        instance = RoomMarker.objects.filter(room__in=obj.rooms.all(), room__type__bookable=True). \
            select_related('room', 'room__type', 'room__type__icon')
        return MobileRoomMarkersSerializer(instance=instance, many=True).data

    def get_room_markers_not_bookable(self, obj):
        instance = RoomMarker.objects.filter(room__in=obj.rooms.all(), room__type__bookable=False). \
            select_related('room', 'room__type', 'room__type__icon')
        return MobileRoomMarkersSerializer(instance=instance, many=True).data

    def get_table_markers(self, obj):
        instance = TableMarker.objects.filter(table__in=self.context['tables']).select_related('table__room')
        return MobileTableMarkersSerializer(instance=instance, many=True).data

    def get_max_room_marker_radius(self, obj):
        room_markers = RoomMarker.objects.filter(room__in=obj.rooms.all())
        if hasattr(obj, 'floormap'):
            return min_radius(room_markers, int(obj.floormap.width), int(obj.floormap.height))
        return 0

    def get_max_table_marker_radius(self, obj):
        if hasattr(obj, 'floormap'):
            max_radius = float(max(obj.floormap.width, obj.floormap.height))
            for room in obj.rooms.all():
                current = min_radius(TableMarker.objects.filter(table__in=room.tables.all()), int(obj.floormap.width),
                                     int(obj.floormap.height))
                if current < max_radius:
                    max_radius = current
            return max_radius
        return 0


class MobileRoomMarkersSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    room_id = serializers.UUIDField()
    is_bookable = serializers.BooleanField(source='room.type.bookable')
    room_marker_x = serializers.DecimalField(source='x', max_digits=4, decimal_places=2)
    room_marker_y = serializers.DecimalField(source='y', max_digits=4, decimal_places=2)
    room_marker_icon = serializers.CharField(source='icon')
    room_type_color = serializers.CharField(source='room.type.color')
    room_type_unified = serializers.BooleanField(source='room.type.unified')
    room_type_title = serializers.CharField(source='room.type.title')
    room_type_thumb = serializers.SerializerMethodField()

    def get_room_type_thumb(self, obj):
        if obj.room.type.icon and obj.room.type.icon.thumb:
            return obj.room.type.icon.thumb
        elif obj.room.type.icon and not obj.room.type.icon.thumb:
            return obj.room.type.icon.path
        else:
            return None

    def to_representation(self, instance):
        response = super(MobileRoomMarkersSerializer, self).to_representation(instance)
        if instance.room.type.unified:
            response['table_id'] = instance.room.tables.first().id
            response['table_title'] = instance.room.tables.first().title
            response['is_available'] = True
        else:
            response['suitable_tables_count'] = instance.room.tables.count()
        return response


class MobileTableMarkersSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    table_id = serializers.UUIDField(source='table.id')
    table_title = serializers.CharField(source='table.title')
    table_marker_x = serializers.DecimalField(source='x', max_digits=4, decimal_places=2)
    table_marker_y = serializers.DecimalField(source='y', max_digits=4, decimal_places=2)
    is_available = serializers.SerializerMethodField()
    room_id = serializers.UUIDField(source='table.room.id')

    def get_is_available(self, obj):
        return True
