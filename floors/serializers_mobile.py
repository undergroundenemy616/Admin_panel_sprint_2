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


class MobileFloorMarkerSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        response = []
        room_markers_bookable = []
        room_markers_not_bookable = []
        table_markers = []
        for marker in instance:
            if marker.bookable and marker.room_marker_id:
                room_marker_bookable = {
                    "id": marker.room_marker_id,
                    "room_id": str(marker.id),
                    "is_bookable": marker.bookable,
                    "room_marker_x": marker.room_marker_x,
                    "room_marker_y": marker.room_marker_y,
                    "room_marker_icon": marker.room_marker_icon,
                    "room_type_color": marker.room_type_color,
                    "room_type_unified": marker.room_type_unified,
                    "room_type_title": marker.room_type_title,
                    "room_type_thumb": marker.room_type_thumb
                }
                if room_marker_bookable.get('room_type_unified'):
                    room_marker_bookable['table_id'] = marker.table_id
                    room_marker_bookable['table_title'] = marker.table_title
                    room_marker_bookable['is_available'] = True if not marker.is_occupied else False
                    room_marker_bookable['tags'] = []
                room_markers_bookable.append(room_marker_bookable)
            elif not marker.bookable and marker.room_marker_id:
                room_marker_not_bookable = {
                    "id": marker.room_marker_id,
                    "room_id": str(marker.id),
                    "is_bookable": marker.bookable,
                    "room_marker_x": marker.room_marker_x,
                    "room_marker_y": marker.room_marker_y,
                    "room_marker_icon": marker.room_marker_icon,
                    "room_type_color": marker.room_type_color,
                    "room_type_unified": marker.room_type_unified,
                    "room_type_title": marker.room_type_title,
                    "room_type_thumb": marker.room_type_thumb
                }
                room_markers_not_bookable.append(room_marker_not_bookable)
            if marker.table_marker_id:
                table_markers.append({
                    "id": marker.table_marker_id,
                    "table_id": str(marker.table_with_marker_id),
                    "table_title": marker.table_title,
                    "table_marker_x": marker.table_marker_x,
                    "table_marker_y": marker.table_marker_y,
                    "is_available": True if not marker.is_occupied else False,
                    "room_id": str(marker.room_id),
                    "tags": []
                })

        for marker in instance:
            for table_marker in table_markers:
                if marker.tag_id and table_marker['table_id'] == str(marker.table_with_marker_id):
                    table_marker['tags'].append(str(marker.tag_id))

        for marker in instance:
            for room_marker in room_markers_bookable:
                if marker.tag_id and str(room_marker.get('table_id')) == str(marker.table_id):
                    room_marker['tags'].append(str(marker.tag_id))

        room_markers_bookable = list({room_marker['id']: room_marker for room_marker in room_markers_bookable}.values())
        room_markers_not_bookable = list({room_marker['id']: room_marker for room_marker in
                                          room_markers_not_bookable}.values())
        table_markers = list({table_marker.get('id'): table_marker for table_marker in table_markers}.values())

        response.append({
            "room_markers_bookable": room_markers_bookable,
            "room_markers_not_bookable": room_markers_not_bookable,
            "table_markers": table_markers
        })

        return response


class MobileFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'title']

