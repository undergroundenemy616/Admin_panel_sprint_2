from typing import Dict, Optional

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, RetrieveModelMixin, CreateModelMixin, \
    DestroyModelMixin, Response, status
from rest_framework.request import Request
from rest_framework import filters
from datetime import datetime

from core.pagination import DefaultPagination
from core.permissions import IsAdmin
from core.mixins import FilterListMixin
from rooms.models import Room, RoomMarker
from rooms.serializers import RoomSerializer, FilterRoomSerializer, CreateRoomSerializer, UpdateRoomSerializer, \
    RoomMarkerSerializer, SwaggerSer
from bookings.models import Booking


class RoomsView(FilterListMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    pagination_class = DefaultPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'type__title', 'description', 'zone__title', 'floor__office__title', 'floor__title']

    permission_classes = (IsAdmin, )

    @staticmethod
    def get_mapped_query(request: Request) -> Optional[Dict]:
        """Returns mapped literals for search in database or None."""
        serializer = FilterRoomSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query_params = serializer.data
        mapped = {"floor_id__in": query_params.get('floor'),
                  "floor__office_id": query_params.get('office'),
                  "type__title__in": query_params.get('type'),
                  "tables__tags__title__in": query_params.get('tags'),
                  "zone_id__in": query_params.get('zone'),
                  }
        items = []
        for field in mapped.keys():
            if not mapped[field]:
                items.append(field)
        for item in items:
            del mapped[item]
        return mapped

    @swagger_auto_schema(query_serializer=SwaggerSer)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('date_to') and request.query_params.get('date_from'):
            rooms = Room.objects.all()
            date_from = datetime.strptime(request.query_params.get('date_from'), '%Y-%m-%dT%H:%M:%S.%f')
            date_to = datetime.strptime(request.query_params.get('date_to'), '%Y-%m-%dT%H:%M:%S.%f')
            if date_from > date_to:
                return Response({"detail": "Not valid data"}, status=status.HTTP_400_BAD_REQUEST)
            response = []
            for room in rooms:
                room_dict = RoomSerializer(instance=room).data
                bookings = Booking.objects.filter(
                    (
                            (Q(date_from__gte=date_from) & Q(date_from__lt=date_to))
                            |
                            (Q(date_from__lte=date_from) & Q(date_to__gte=date_to))
                            |
                            (Q(date_to__gt=date_from) & Q(date_to__lte=date_to))
                    )
                )
                for booking in bookings:
                    room_tables = room_dict['tables'][:]
                    for table in room_dict['tables']:
                        if table.get('id') == str(booking.table_id):
                            room_tables.remove(table)
                    room_dict['tables'] = room_tables
                response.append(room_dict)
            return Response({'results': response}, status=200)

        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        self.serializer_class = CreateRoomSerializer
        return self.create(request, *args, **kwargs)


class DetailRoomView(RetrieveModelMixin,
                     UpdateModelMixin,
                     DestroyModelMixin,
                     GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    pagination_class = DefaultPagination

    permission_classes = (IsAdmin,)

    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateRoomSerializer
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RoomMarkerView(CreateModelMixin,
                     DestroyModelMixin,
                     GenericAPIView):
    queryset = RoomMarker.objects.all()
    serializer_class = RoomMarkerSerializer
    permission_classes = (IsAdmin, )

    def post(self, request, *args, **kwargs):
        room_instance = Room.objects.filter(id=request.data['room']).first()
        if room_instance:
            if hasattr(room_instance, 'room_marker'):
                instance = RoomMarker.objects.filter(id=room_instance.room_marker.id).first()
            else:
                instance = None
        else:
            instance = None
        if instance:
            serializer = self.serializer_class(data=request.data, instance=instance)
        else:
            serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.serializer_class = RoomSerializer
        serializer = self.serializer_class(instance=instance.room)
        return Response(serializer.to_representation(instance=instance.room), status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        room_instance = get_object_or_404(Room, pk=request.data['room'])
        instance = get_object_or_404(RoomMarker, pk=room_instance.room_marker.id)
        instance.delete()
        self.serializer_class = RoomSerializer
        room_instance = get_object_or_404(Room, pk=request.data['room'])  # Need to fix to improve performance
        serializer = self.serializer_class(instance=room_instance)
        return Response(serializer.to_representation(instance=room_instance), status=status.HTTP_200_OK)
