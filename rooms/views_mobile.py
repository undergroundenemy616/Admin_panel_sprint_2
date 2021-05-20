import uuid
from datetime import datetime

import orjson
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Prefetch, Count
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, Response, status

from bookings.models import Booking
from core.pagination import DefaultPagination
from core.permissions import IsAuthenticated
from files.serializers_mobile import MobileBaseFileSerializer
from groups.models import Group, ADMIN_ACCESS
from offices.models import OfficeZone
from rooms.models import Room, RoomType
from rooms.serializers import SwaggerRoomParameters, TestRoomSerializer
from rooms.serializers_mobile import (MobileRoomGetSerializer,
                                      MobileRoomSerializer,
                                      SuitableRoomParameters,
                                      MobileShortRoomSerializer)
from tables.models import Table
from tables.serializers_mobile import MobileTableSerializer


class SuitableRoomsMobileView(GenericAPIView):
    queryset = Room.objects.all()
    serializer_class = TestRoomSerializer
    pagination_class = None
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(query_serializer=SuitableRoomParameters)
    def get(self, request, *args, **kwargs):
        serializer = SuitableRoomParameters(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        office = serializer.data.get('office')
        date_from = serializer.data.get('date_from')
        date_to = serializer.data.get('date_to')
        quantity = serializer.data.get('quantity')
        room_type_title = serializer.data.get('type')

        try:
            room_type = RoomType.objects.get(title=room_type_title, office_id=office, bookable=True)
        except ObjectDoesNotExist:
            return Response("Type not found", status=status.HTTP_404_NOT_FOUND)

        rooms = Room.objects.filter(floor__office_id=office, type=room_type)

        tables = Table.objects.filter(room__id__in=rooms, is_occupied=False).select_related('table_marker', 'room',
                                                                                            'room__floor', 'room__zone')

        bookings = Booking.objects.filter(Q(table__id__in=tables, status__in=['waiting', 'active']) &
                                          (Q(date_from__lt=date_to, date_to__gte=date_to)
                                           | Q(date_from__lte=date_from, date_to__gt=date_from)
                                           | Q(date_from__gte=date_from, date_to__lte=date_to)) &
                                          Q(date_from__lt=date_to)).values_list('table__id', flat=True)

        tables = tables.exclude(id__in=bookings)

        response = []

        if tables.count() < quantity:
            quantity = tables.count()

        for table in tables:
            if not room_type.unified and len(response) != quantity:
                try:
                    if table.table_marker:
                        response.append({
                            'room': {
                                'id': str(table.room.id),
                                'title': table.room.title
                            },
                            'floor': {
                                'id': str(table.room.floor.id),
                                'title': table.room.floor.title
                            },
                            'zone': {
                                'id': str(table.room.zone.id),
                                'title': table.room.zone.title
                            },
                            'table': {
                                'id': str(table.id),
                                'title': table.title,
                                'images': MobileBaseFileSerializer(instance=table.images, many=True).data
                            }
                        })
                except Table.table_marker.RelatedObjectDoesNotExist:
                    pass
            elif room_type.unified and len(response) != quantity:
                try:
                    if table.room.room_marker:
                        response.append({
                            'room': {
                                'id': str(table.room.id),
                                'title': table.room.title
                            },
                            'floor': {
                                'id': str(table.room.floor.id),
                                'title': table.room.floor.title
                            },
                            'zone': {
                                'id': str(table.room.zone.id),
                                'title': table.room.zone.title
                            },
                            'table': {
                                'id': str(table.id),
                                'title': table.title,
                                'images': MobileBaseFileSerializer(instance=table.images, many=True).data
                            }
                        })
                except Room.room_marker.RelatedObjectDoesNotExist:
                    pass
            else:
                break

        if response:
            return Response(orjson.loads(orjson.dumps(response)), status=status.HTTP_200_OK)
        else:
            return Response("Suitable places not found", status=status.HTTP_200_OK)


class MobileRoomsView(GenericAPIView,
                      ListModelMixin):
    serializer_class = MobileRoomSerializer
    queryset = Room.objects.all().select_related('type', 'floor', 'zone', 'room_marker').prefetch_related('images')
    pagination_class = DefaultPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'type__title', 'description']

    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        queryset = self.queryset
        account_groups = self.request.user.account.groups.all()
        # kiosk_groups = Group.objects.filter(title='Информационный киоск').first()   # TODO fix title for this
        access = [access_dict.get('access') for access_dict in account_groups.values('access')]
        if not access:
            return self.queryset.none()
        if min(access) <= ADMIN_ACCESS:
            return queryset.all()
        else:
            visitor_group = Group.objects.filter(title='Посетитель', is_deletable=False)
            account_groups = list(account_groups.values_list('id', flat=True)) + list(
                visitor_group.values_list('id', flat=True))
            zones = OfficeZone.objects.filter(groups__id__in=account_groups)
            return self.queryset.filter(zone__in=zones)

    @swagger_auto_schema(query_serializer=SwaggerRoomParameters)
    def get(self, request, *args, **kwargs):
        serializer = MobileRoomGetSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        self.queryset = self.get_queryset()
        if request.query_params.get('search'):
            by_office = self.queryset.filter(floor__office=request.query_params.get('office'))
            self.queryset = by_office
            return self.list(request, *args, **kwargs)
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

        response = TestRoomSerializer(instance=rooms.prefetch_related('tables',
                                                                      'tables__tags',
                                                                      'tables__images',
                                                                      'tables__table_marker',
                                                                      'type__icon',
                                                                      'images').select_related(
                                'room_marker', 'type', 'floor', 'zone'), many=True).data

        if request.query_params.getlist('tags'):
            tables = Table.objects.all().prefetch_related(
                'tags', 'images').select_related('table_marker').distinct()
            for tag in request.query_params.getlist('tags'):
                tables = tables.filter(tags__title__icontains=tag)
            serialized_tables = MobileTableSerializer(instance=tables, many=True).data
            i = 0
            while i < len(response):
                tables_with_tags = []
                for table in serialized_tables:
                    if str(table['room']) == response[i]['id']:
                        tables_with_tags.append(table)
                response[i]['tables'] = tables_with_tags
                if len(response[i]['tables']) == 0:
                    response.remove(response[i])
                else:
                    response[i]['suitable_tables'] = len(response[i]['tables'])
                    i += 1

        if request.query_params.get('date_to') and request.query_params.get('date_from'):
            date_from = datetime.strptime(request.query_params.get('date_from'), '%Y-%m-%dT%H:%M:%S.%f')
            date_to = datetime.strptime(request.query_params.get('date_to'), '%Y-%m-%dT%H:%M:%S.%f')

            bookings = Booking.objects.filter(status__in=['active', 'waiting']).filter(
                (
                        (Q(date_from__gte=date_from) & Q(date_from__lt=date_to))
                        |
                        (Q(date_from__lte=date_from) & Q(date_to__gte=date_to))
                        |
                        (Q(date_to__gt=date_from) & Q(date_to__lte=date_to))
                )
            ).filter(table__room_id__in=rooms).select_related('table').values_list('table__id', flat=True)

            if date_from > date_to:
                return Response({"detail": "Not valid data"}, status=status.HTTP_400_BAD_REQUEST)

            if request.headers._store.get('version'):
                for room in response:
                    room_tables = room['tables'][:]
                    for table in room['tables']:
                        if not table.get('marker') and not room['room_type_unified']:
                            room_tables.remove(table)
                            continue
                        if uuid.UUID(table.get('id')) in bookings:
                            table['is_available'] = False
                            room['suitable_tables'] -= 1
                        else:
                            table['is_available'] = True
                    room['tables'] = room_tables
            else:
                "Made for old Version.1 of mobile app"
                for room in response:
                    room_tables = room['tables'][:]
                    for table in room['tables']:
                        if (not table.get('marker') and not room['room_type_unified']) or uuid.UUID(
                                table.get('id')) in bookings:
                            table['is_available'] = False
                            room_tables.remove(table)
                        else:
                            table['is_available'] = True
                        if room['room_type_unified'] and uuid.UUID(table.get('id')) in bookings:
                            room['booked_table'] = table
                    room['tables'] = room_tables
                copy_response = response[:]
                for room in copy_response:
                    if len(room['tables']) == 0:
                        response.remove(room)

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

        suitable_tables = 0

        for room in response:
            suitable_tables += len(room.get('tables'))

        response_dict = {
            'results': response,
            'suitable_tables': suitable_tables
        }
        return Response(response_dict, status=status.HTTP_200_OK)


class MobileRoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = MobileShortRoomSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.method == "GET":
            return self.queryset.select_related('type')
