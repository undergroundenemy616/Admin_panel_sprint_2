from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import QuerySet, Value
from rest_framework import serializers

from floors.models import Floor
from files.serializers_mobile import MobileBaseFileSerializer
from rooms.models import RoomMarker, Room
from tables.models import TableMarker


def min_radius(markers: QuerySet) -> int:
    min_val = 100
    values = list(markers.values_list('x', 'y'))
    for i in range(len(values)):
        for j in range(i+1, len(values)):
            current = ((float(values[i][0] - values[j][0]))**2 + float((values[i][1] - values[j][1]))**2)**0.5
            if current < min_val:
                min_val = current
    return min_val


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


class MobileFloorMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'

    def to_representation(self, instance):
        response = []
        room_markers_bookable = []
        room_markers_not_bookable = []
        table_markers = []

        for room in instance.rooms.all():
            try:
                if room.type.bookable and room.room_marker:
                    room_marker_bookable = {
                        "id": room.room_marker.id,
                        "room_id": str(room.id),
                        "is_bookable": room.type.bookable,
                        "room_marker_x": room.room_marker.x,
                        "room_marker_y": room.room_marker.y,
                        "room_marker_icon": room.room_marker.icon,
                        "room_type_color": room.type.color,
                        "room_type_unified": room.type.unified,
                        "room_type_title": room.type.title,
                    }
                    if room.type.icon and room.type.icon.thumb:
                        room_marker_bookable["room_type_thumb"] = room.type.icon.thumb
                    elif room.type.icon and not room.type.icon.thumb:
                        room_marker_bookable["room_type_thumb"] = room.type.icon.path
                    else:
                        room_marker_bookable["room_type_thumb"] = None
                    if room.type.unified:
                        for table in room.tables.all():
                            room_marker_bookable['table_id'] = table.id
                            room_marker_bookable['table_title'] = table.title
                            room_marker_bookable['is_available'] = True if not table.is_occupied else False
                    room_markers_bookable.append(room_marker_bookable)
                elif not room.type.bookable and room.room_marker.id:
                    room_marker_not_bookable = {
                        "id": room.room_marker.id,
                        "room_id": str(room.id),
                        "is_bookable": room.type.bookable,
                        "room_marker_x": room.room_marker.x,
                        "room_marker_y": room.room_marker.y,
                        "room_marker_icon": room.room_marker.icon,
                        "room_type_color": room.type.color,
                        "room_type_unified": room.type.unified,
                        "room_type_title": room.type.title,
                    }
                    if room.type.icon and room.type.icon.thumb:
                        room_marker_not_bookable["room_type_thumb"] = room.type.icon.thumb
                    elif room.type.icon and not room.type.icon.thumb:
                        room_marker_not_bookable["room_type_thumb"] = room.type.icon.path
                    else:
                        room_marker_not_bookable["room_type_thumb"] = None
                    room_markers_not_bookable.append(room_marker_not_bookable)
            except ObjectDoesNotExist:
                pass

            for table in room.tables.all():
                try:
                    table_markers.append({
                        "id": table.table_marker.id,
                        "table_id": str(table.id),
                        "table_title": table.title,
                        "table_marker_x": table.table_marker.x,
                        "table_marker_y": table.table_marker.y,
                        "is_available": True if not table.is_occupied else False,
                        "room_id": str(table.room_id),
                    })
                except ObjectDoesNotExist:
                    pass

        response.append({
            "room_markers_bookable": room_markers_bookable,
            "room_markers_not_bookable": room_markers_not_bookable,
            "table_markers": table_markers
        })

        return response


class MobileNewFloorMarkerSerializer(serializers.Serializer):
    room_markers_bookable = serializers.SerializerMethodField()
    room_markers_not_bookable = serializers.SerializerMethodField()
    table_markers = serializers.SerializerMethodField()
    max_room_marker_radius = serializers.SerializerMethodField()
    
    def __init__(self, *args, **kwargs):
        super(MobileNewFloorMarkerSerializer, self).__init__(*args, **kwargs)

    def get_room_markers_bookable(self, obj):
        instance = RoomMarker.objects.filter(room__in=Room.objects.filter(floor=obj), room__type__bookable=True).\
            select_related('room', 'room__type', 'room__type__icon')
        return MobileRoomMarkersSerializer(instance=instance, many=True).data

    def get_room_markers_not_bookable(self, obj):
        instance = RoomMarker.objects.filter(room__in=Room.objects.filter(floor=obj), room__type__bookable=False).\
            select_related('room', 'room__type', 'room__type__icon')
        return MobileRoomMarkersSerializer(instance=instance, many=True).data

    def get_table_markers(self, obj):
        max_radius = 100
        for room in obj.rooms.all():
            current = min_radius(TableMarker.objects.filter(table__in=room.tables.all()))
            if current < max_radius:
                max_radius = current
        instance = TableMarker.objects.filter(table__room__floor=obj).select_related('table__room').annotate(
            max_table_marker_radius=Value(max_radius, output_field=models.FloatField())
        )
        return MobileTableMarkersSerializer(instance=instance, many=True).data

    def get_max_room_marker_radius(self, obj):
        room_markers = RoomMarker.objects.filter(room__in=Room.objects.filter(floor=obj))
        return min_radius(room_markers)


class MobileRoomMarkersSerializer(serializers.Serializer):
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
            response['is_available'] = not instance.room.tables.first().is_occupied
        return response


class MobileTableMarkersSerializer(serializers.Serializer):
    table_title = serializers.CharField(source='table.title')
    table_marker_x = serializers.DecimalField(source='x', max_digits=4, decimal_places=2)
    table_marker_y = serializers.DecimalField(source='y', max_digits=4, decimal_places=2)
    is_available = serializers.BooleanField(source='table.is_occupied')
    room_id = serializers.UUIDField(source='table.room.id')
    max_table_marker_radius = serializers.FloatField()
