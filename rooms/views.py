import uuid
from datetime import datetime
from typing import Dict, Optional

import orjson
from django.db.models import Prefetch, Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, Response,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   status)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request

from bookings.models import Booking
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from floors.models import Floor
from groups.models import ADMIN_ACCESS, GUEST_ACCESS, Group
from offices.models import Office, OfficeZone
from rooms.models import Room, RoomMarker
from rooms.serializers import (CreateRoomSerializer, FilterRoomSerializer,
                               RoomGetSerializer, RoomMarkerSerializer,
                               RoomSerializer, RoomSerializerCSV,
                               SwaggerRoomParameters, TestRoomSerializer,
                               UpdateRoomSerializer, base_serialize_room,
                               table_serializer_for_room)
from tables.serializers import Table, TableSerializer, TestTableSerializer


class RoomsView(ListModelMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all().select_related('type', 'floor', 'zone', 'room_marker').prefetch_related('images')
    pagination_class = DefaultPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'type__title', 'description']

    permission_classes = (IsAuthenticated, )

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

    # def get_queryset(self, *args, **kwargs):
    #     queryset = self.queryset
    #     account_groups = self.request.user.account.groups.all()
    #     kiosk_groups = Group.objects.filter(title='Информационный киоск').first()   # TODO fix title for this
    #     access = [access_dict.get('access') for access_dict in account_groups.values('access')]
    #     if not access:
    #         return self.queryset.none()
    #     coworking_zone = OfficeZone.objects.filter(title='Зона коворкинга')
    #
    #     if kiosk_groups in account_groups:
    #         return queryset.filter(zone__in=coworking_zone)
    #     elif min(access) <= ADMIN_ACCESS:
    #         return queryset.all()
    #     else:
    #         visitor_group = Group.objects.filter(title='Посетитель', is_deletable=False)
    #         account_groups = list(account_groups.values_list('id', flat=True)) + list(
    #             visitor_group.values_list('id', flat=True))
    #         zones = OfficeZone.objects.filter(groups__id__in=account_groups)
    #         return self.queryset.filter(zone__in=zones)

    @swagger_auto_schema(query_serializer=SwaggerRoomParameters)
    def get(self, request, *args, **kwargs):
        serializer = RoomGetSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # self.queryset = self.get_queryset()
        if request.query_params.get('search'):
            by_office = self.queryset.filter(floor__office=request.query_params.get('office'))
            self.queryset = by_office
            return self.list(request, *args, **kwargs)
        response = []
        if request.query_params.get('office'):
            rooms = self.queryset.exclude(type_id__isnull=True, type__bookable=False).\
                filter(floor__office_id=request.query_params.get('office'))
        elif request.query_params.get('floor'):
            rooms = self.queryset.exclude(type_id__isnull=True).\
                filter(floor_id=request.query_params.get('floor'))
        else:
            return Response({"detail": "You must specify at least on of this fields: " +
                                       "'office' or 'floor'"}, status=status.HTTP_400_BAD_REQUEST)

        if request.query_params.get('zone'):
            rooms = rooms.filter(zone_id=request.query_params.get('zone'))

        if request.query_params.get('type'):
            rooms = rooms.filter(type__title=request.query_params.get('type'))

        # for room in rooms.prefetch_related('tables'):  # This for cycle slowing down everything, because of a huge amount of data being serialized in it, and i don`t know how to fix it
        #     response.append(base_serialize_room(room=room).copy())
        response = TestRoomSerializer(instance=rooms.prefetch_related('tables', 'tables__tags', 'tables__images', 'tables__table_marker', 'type__icon', 'images').select_related(
                                'room_marker', 'type', 'floor', 'zone'), many=True).data
        # return Response(orjson.loads(orjson.dumps(response)))   # Made for test

        if request.query_params.get('date_to') and request.query_params.get('date_from'):
            date_from = datetime.strptime(request.query_params.get('date_from'), '%Y-%m-%dT%H:%M:%S.%f')
            date_to = datetime.strptime(request.query_params.get('date_to'), '%Y-%m-%dT%H:%M:%S.%f')

            if date_from > date_to:
                return Response({"detail": "Not valid data"}, status=status.HTTP_400_BAD_REQUEST)
            for room in response:
                bookings = Booking.objects.filter(status__in=['active', 'waiting']).filter(
                    (
                            (Q(date_from__gte=date_from) & Q(date_from__lt=date_to))
                            |
                            (Q(date_from__lte=date_from) & Q(date_to__gte=date_to))
                            |
                            (Q(date_to__gt=date_from) & Q(date_to__lte=date_to))
                    )
                ).select_related('table').values_list('table__id', flat=True)
                room_tables = room['tables'][:]
                for table in room['tables']:
                    if (not table.get('marker') and not room['room_type_unified']) or uuid.UUID(table.get('id')) in bookings:
                        room_tables.remove(table)
                room['tables'] = room_tables
                # for booking in bookings:
                #     room_tables = room['tables'][:]
                #     for table in room['tables']:
                #         if table.get('id') == str(booking.table_id):
                #             room_tables.remove(table)
                #     room['tables'] = room_tables

        if request.query_params.get('range_to') and request.query_params.get('range_from'):
            not_in_range = []
            range_to = int(request.query_params.get('range_to'))
            range_from = int(request.query_params.get('range_from'))
            if range_to is not None and range_from > range_to:
                return Response({"detail": "Not valid data"}, status=status.HTTP_400_BAD_REQUEST)
            for room in response:
                if (range_to is not None and len(room.get('tables')) not in range(range_from, range_to + 1)) or \
                        (range_to is None and len(room.get('tables')) < range_from):
                    not_in_range.append(room)
            for room in not_in_range:
                response.remove(room)

        if request.query_params.get('marker') and int(request.query_params.get('marker')) == 1:
            with_marker = []
            for room in response:
                if room['marker']:
                    with_marker.append(room)
            response = with_marker

        if request.query_params.get('image') is not None:
            if int(request.query_params.get('image')) == 1:
                with_image = []
                for room in response:
                    if room['images']:
                        with_image.append(room)
                response = with_image
            elif int(request.query_params.get('image')) == 0:
                without_image = []
                for room in response:
                    if not room['images']:
                        without_image.append(room)
                response = without_image

        if request.query_params.getlist('tags'):
            tables = Table.objects.all().filter(tags__title__in=request.query_params.getlist('tags')).prefetch_related('tags', 'images').select_related('table_marker')
            for room in response:
                tables_with_tags = []
                serialized_tables = TestTableSerializer(instance=tables, many=True).data
                for table in serialized_tables:
                    if str(table['room']) == room['id']:
                        tables_with_tags.append(table)
                room['tables'] = tables_with_tags

        suitable_tables = 0

        for room in response:
            suitable_tables += len(room.get('tables'))

        response_dict = {
            'results': response,
            'suitable_tables': suitable_tables
        }

        # return Response(orjson.loads(orjson.dumps(response_dict)), status=status.HTTP_200_OK)
        return Response(response_dict, status=status.HTTP_200_OK)

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
        self.serializer_class = TestRoomSerializer
        serializer = self.serializer_class(instance=instance.room)
        return Response(serializer.to_representation(instance=instance.room), status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'room': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        }
    ))
    def delete(self, request, *args, **kwargs):
        room_instance = get_object_or_404(Room, pk=request.data['room'])
        instance = get_object_or_404(RoomMarker, room=room_instance)
        instance.delete()
        self.serializer_class = RoomSerializer
        room_instance = get_object_or_404(Room, pk=request.data['room'])  # Need to fix to improve performance
        serializer = self.serializer_class(instance=room_instance)
        return Response(serializer.to_representation(instance=room_instance), status=status.HTTP_200_OK)


class ListCreateRoomCsvView(GenericAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializerCSV
    pagination_class = None
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        rooms = serializer.save()
        return Response(rooms, status=status.HTTP_200_OK)
