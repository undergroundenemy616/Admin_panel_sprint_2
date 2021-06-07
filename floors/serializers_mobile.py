from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from floors.models import Floor
from files.serializers_mobile import MobileBaseFileSerializer


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
