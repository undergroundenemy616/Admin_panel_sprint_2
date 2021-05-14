from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from floors.models import Floor, FloorMap
from floors.serializers import floor_map_serializer, TestFloorSerializerWithMap
from offices.models import Office
from rooms.serializers import TestRoomSerializer
from tables.models import Table

class PanelFileSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    path = serializers.CharField()
    thumb = serializers.CharField()


class PanelSingleTableSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    is_occupied = serializers.BooleanField()


class PanelRoomGetSerializer(serializers.Serializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)


class PanelSingleRoomSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    tables = PanelSingleTableSerializer(many=True, required=False)
    images = PanelFileSerializer(many=True, required=False)

    def to_representation(self, instance):
        response = super(PanelSingleRoomSerializer, self).to_representation(instance)
        for table in instance.tables.all():
            if table.is_occupied:
                response['status'] = 'occupied'
            else:
                response['status'] = 'not occupied'
        return response


class PanelFloorSerializerWithMap(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all())

    def to_representation(self, instance):
        response = super(PanelFloorSerializerWithMap, self).to_representation(instance)
        response['rooms'] = TestRoomSerializer(
            instance=instance.rooms.filter(type__unified=True).prefetch_related('tables', 'tables__tags', 'tables__images', 'tables__table_marker',
                                                     'type__icon', 'images').select_related(
                'room_marker', 'type', 'floor', 'zone'), many=True).data
        tables = Table.objects.filter(room__floor=instance)
        try:
            response['floor_map'] = floor_map_serializer(floor_map=FloorMap.objects.get(floor=instance))
        except ObjectDoesNotExist:
            response['floor_map'] = None
        response['occupied'] = tables.filter(is_occupied=True).count()
        response['capacity'] = tables.count()
        response['capacity_meeting'] = tables.filter(room__type__unified=True).count()
        response['occupied_meeting'] = tables.filter(room__type__unified=True, is_occupied=True).count()
        response['capacity_tables'] = tables.filter(room__type__unified=False).count()
        response['occupied_tables'] = tables.filter(room__type__unified=False, is_occupied=True).count()
        return response
