from rest_framework import serializers

from floors.models import Floor
from offices.models import Office, OfficeZone
from rooms.models import Room, RoomMarker
from rooms.serializers import table_tags_validator, type_validatior
from tables.serializers_mobile import MobileTableSerializer


class SuitableRoomParameters(serializers.Serializer):
    office = serializers.UUIDField(required=True)
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    type = serializers.CharField(required=True)
    quantity = serializers.IntegerField(required=True)


class MobileRoomSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    tables = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    images = serializers.PrimaryKeyRelatedField(read_only=True, many=True, required=False)
    type = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    class Meta:
        model = Room
        fields = '__all__'  # ['tables', 'images', 'type']

    def to_representation(self, instance):
        response = super(MobileRoomSerializer, self).to_representation(instance)
        response['floor'] = {"id": instance.floor.id, "title": instance.floor.title}
        response['zone'] = {"id": instance.zone.id, "title": instance.zone.title}
        response['type'] = instance.type.title if instance.type else None
        response['room_type_color'] = instance.type.color if instance.type else None
        response['room_type_unified'] = instance.type.unified if instance.type else None
        response['is_bookable'] = instance.type.bookable if instance.type else None
        response['room_type_icon'] = instance.type.icon if instance.type else None
        response['tables'] = MobileTableSerializer(instance=instance.tables.prefetch_related('tags', 'images').select_related('table_marker'), many=True).data
        response['capacity'] = instance.tables.count()
        response['marker'] = MobileRoomMarkerSerializer(instance=instance.room_marker).data if \
            hasattr(instance, 'room_marker') else None
        response['occupied'] = instance.tables.filter(is_occupied=True).count(),
        response['suitable_tables'] = instance.tables.filter(is_occupied=False).count()
        return response


class MobileRoomGetSerializer(serializers.Serializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    zone = serializers.PrimaryKeyRelatedField(queryset=OfficeZone.objects.all(), required=False)
    type = serializers.CharField(validators=[type_validatior], required=False)
    date_to = serializers.DateTimeField(required=False)
    date_from = serializers.DateTimeField(required=False)
    tags = serializers.ListField(validators=[table_tags_validator], required=False)


class MobileRoomMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMarker
        exclude = ['room']


class MobileShortRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'title']

    def to_representation(self, instance):
        response = super(MobileShortRoomSerializer, self).to_representation(instance)
        response['room'] = {
            'id': instance.id,
            'title': instance.title,
            'type': instance.type.title if instance.type else None
        }
        return response
