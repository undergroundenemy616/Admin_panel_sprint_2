from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, Response,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   status)
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework import filters

from rooms.models import Room
from core.permissions import IsAdmin
from rooms.serializers import TestRoomSerializer, RoomSerializer
from rooms.serializers_panel import PanelRoomGetSerializer


class PanelRoomsView(GenericAPIView, ListModelMixin):
    queryset = Room.objects.all().select_related('type', 'floor', 'zone', 'room_marker').prefetch_related('images')
    permission_classes = (IsAdmin, )
    serializer_class = RoomSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'type__title', 'description']
    pagination_class = None

    def get(self, request, *args, **kwargs):
        serializer = PanelRoomGetSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        self.queryset = self.get_queryset()
        if request.query_params.get('search'):
            unified_rooms_on_floor_for_search = self.queryset.filter(floor=request.query_params.get('floor'), type__unified=True)
            self.queryset = unified_rooms_on_floor_for_search
            results = self.list(request, *args, **kwargs)
            response_dict = {
                'results': results.data
            }
            return Response(response_dict, status=status.HTTP_200_OK)
        unified_rooms_on_floor = self.queryset.filter(floor=request.query_params.get('floor'), type__unified=True)
        response = TestRoomSerializer(
            instance=unified_rooms_on_floor.prefetch_related('tables', 'tables__tags', 'tables__images', 'tables__table_marker',
                                            'type__icon', 'images').select_related(
                'room_marker', 'type', 'floor', 'zone'), many=True).data

        copy_response = response[:]
        for room in copy_response:
            if len(room["tables"]) == 0:
                response.remove(room)

        suitable_tables = 0

        for room in response:
            suitable_tables += len(room.get('tables'))

        response_dict = {
            'results': response,
            'suitable_tables': suitable_tables
        }
        return Response(response_dict, status=status.HTTP_200_OK)

