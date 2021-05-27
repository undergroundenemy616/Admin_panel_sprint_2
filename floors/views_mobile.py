from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, When, Case
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, Response, status
import uuid

from bookings.models import Booking
from core.handlers import ResponseException
from core.pagination import DefaultPagination
from core.permissions import IsAdminOrReadOnly, IsAuthenticated
from floors.models import Floor, FloorMap
from floors.serializers import SwaggerFloorParameters
from floors.serializers_mobile import (MobileFloorMapBaseSerializer,
                                       MobileFloorMarkerParameters,
                                       MobileFloorMarkerSerializer,
                                       MobileFloorSerializer,
                                       MobileFloorSuitableParameters)
from rooms.models import RoomType
from tables.models import Table


class MobileListFloorMapView(GenericAPIView):
    queryset = FloorMap.objects.all()
    serializer_class = MobileFloorMapBaseSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = DefaultPagination

    def get(self, request, pk=None, *args, **kwargs):
        try:
            floor = Floor.objects.get(id=pk)
        except ObjectDoesNotExist:
            raise ResponseException("Floor not found", status_code=status.HTTP_404_NOT_FOUND)
        try:
            floor_map = self.serializer_class(instance=floor.floormap).data
        except FloorMap.DoesNotExist:
            floor_map = {}
        response = {
            'id': str(floor.id),
            'title': floor.title,
            'floor_map': floor_map
        }
        return Response(response, status=status.HTTP_200_OK)


class MobileFloorMarkers(GenericAPIView):
    queryset = Floor.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = MobileFloorMarkerSerializer

    @swagger_auto_schema(query_serializer=MobileFloorMarkerParameters)
    def get(self, request, pk=None, *args, **kwargs):
        serializer = MobileFloorMarkerParameters(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        date_from = serializer.data.get('date_from')
        date_to = serializer.data.get('date_to')
        tag = serializer.data.get('tag')

        try:
            floor = self.queryset.get(id=pk)
        except ObjectDoesNotExist:
            raise ResponseException("Floor not found", status_code=status.HTTP_404_NOT_FOUND)

        query = f"""
        SELECT rr.id          as id,
        rtr.bookable,
        rm.id          as room_marker_id,
        rm.x           as room_marker_x,
        rm.y           as room_marker_y,
        rm.icon        as room_marker_icon,
        rtr.color      as room_type_color,
        rtr.unified    as room_type_unified,
        rtr.title      as room_type_title,
        tm.id          as table_marker_id,
        tm.table_id    as table_with_marker_id,
        tm.x           as table_marker_x,
        tm.y           as table_marker_y,
        tt.id          as table_id,
        tt.title       as table_title,
        tt.is_occupied as is_occupied,
        tt.room_id     as room_id,
        f.thumb        as room_type_thumb,
        ff.id          as floor_id,
        tg.id          as tag_id,
        tg.title       as tag_title
        FROM floors_floor as ff
        JOIN rooms_room rr on ff.id = rr.floor_id
        JOIN room_types_roomtype rtr on rr.type_id = rtr.id
        LEFT JOIN rooms_roommarker rm on rr.id = rm.room_id
        LEFT JOIN tables_table tt on rr.id = tt.room_id
        LEFT JOIN tables_tablemarker tm on tt.id = tm.table_id
        LEFT JOIN files_file f on rtr.icon_id = f.id
        LEFT JOIN tables_table_tags ttt on tt.id = ttt.table_id
        LEFT JOIN tables_tabletag tg on ttt.tabletag_id = tg.id
        WHERE ff.id = '{floor.id}'"""

        if serializer.data.get('room_type'):
            try:
                room_type = RoomType.objects.get(title=serializer.data.get('room_type'),
                                                 office_id=floor.office.id)
            except ObjectDoesNotExist:
                raise ResponseException("RoomType not found", status_code=status.HTTP_404_NOT_FOUND)

            if room_type.title == "Рабочее место":
                query = query + f"""and rtr.title != 'Переговорная'"""
            elif room_type.title == "Переговорная":
                query = query + f"""and rtr.title != 'Рабочее место'"""

        sql_results = self.queryset.raw(query)

        if sql_results:
            markers = self.serializer_class(instance=sql_results).data
        else:
            return Response([], status=status.HTTP_200_OK)

        if date_from and date_to:
            bookings = Booking.objects.filter(Q(status__in=['waiting', 'active']) &
                                              (Q(date_from__lt=date_to, date_to__gte=date_to)
                                               | Q(date_from__lte=date_from, date_to__gt=date_from)
                                               | Q(date_from__gte=date_from, date_to__lte=date_to)) &
                                              Q(date_from__lt=date_to)).values_list('table__id', flat=True)

            if bookings:
                for table_marker in markers[0]['table_markers']:
                    if uuid.UUID(table_marker.get('table_id')) in list(bookings):
                        table_marker['is_available'] = False
                for room_marker in markers[0]['room_markers_bookable']:
                    if room_marker.get('table_id') in list(bookings):
                        room_marker['is_available'] = False

        if tag:
            filtered_tables = []
            filtered_rooms = []

            for table_marker in markers[0]['table_markers']:
                if set(tag).issubset(set(table_marker.get('tags'))):
                    filtered_tables.append(table_marker)

            markers[0]['table_markers'] = filtered_tables

            for room_marker in markers[0]['room_markers_bookable']:
                if room_marker.get('tags') and set(tag).issubset(set(room_marker.get('tags'))) \
                        and room_marker not in filtered_rooms:
                    filtered_rooms.append(room_marker)

            markers[0]['room_markers_bookable'] = filtered_rooms

        for room_marker in markers[0]['room_markers_bookable']:
            room_marker.pop('tags', None)

        return Response(markers, status=status.HTTP_200_OK)


class MobileListFloorView(ListModelMixin,
                          GenericAPIView):
    """Floors API View."""
    queryset = Floor.objects.all().prefetch_related('office').select_related('office')
    pagination_class = None
    serializer_class = MobileFloorSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerFloorParameters)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('office'):
            self.queryset = self.queryset.all().filter(office=request.query_params.get('office'))

        return self.list(request, *args, **kwargs)


class MobileSuitableFloorView(GenericAPIView):
    queryset = Floor.objects.all()
    serializer_class = MobileFloorSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=MobileFloorSuitableParameters)
    def get(self, request, *args, **kwargs):
        date_to = request.query_params.get('date_to')
        date_from = request.query_params.get('date_from')
        bookings = Booking.objects.filter(Q(status__in=['waiting', 'active'])
                                          &
                                          (Q(date_from__lt=date_to, date_to__gte=date_to) |
                                           Q(date_from__lte=date_from, date_to__gt=date_from) |
                                           Q(date_from__gte=date_from, date_to__lte=date_to))
                                          &
                                          Q(date_from__lt=date_to)).values_list('table__id', flat=True)

        serializer = MobileFloorSuitableParameters(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        tag = serializer.data.get('tag')
        count = 0

        if tag:
            try:
                room_type = RoomType.objects.get(office_id=request.query_params.get('office'),
                                                 title=request.query_params.get('room_type'))
            except RoomType.DoesNotExist:
                raise ResponseException("Room Type not found", status_code=status.HTTP_404_NOT_FOUND)

            if room_type.unified:
                tables_count = Table.objects.filter(Q(room__floor__in=self.queryset)
                                                    &
                                                    Q(is_occupied=False)
                                                    &
                                                    Q(room__type__title=room_type.title)
                                                    &
                                                    Q(room__room_marker__isnull=False)
                                                    &
                                                    Q(table_marker__isnull=True)
                                                    &
                                                    ~Q(id__in=bookings)).select_related('table_marker',
                                                                                        'room__floor',
                                                                                        'room').prefetch_related('tags')
            else:
                tables_count = Table.objects.filter(Q(room__floor__in=self.queryset)
                                                    &
                                                    Q(is_occupied=False)
                                                    &
                                                    Q(room__type__title=room_type.title)
                                                    &
                                                    Q(room__room_marker__isnull=False)
                                                    &
                                                    Q(table_marker__isnull=False)
                                                    &
                                                    ~Q(id__in=bookings)).select_related('table_marker',
                                                                                        'room__floor',
                                                                                        'room').prefetch_related('tags')

            for t in list(tag):
                tables_count = tables_count.filter(tags__id=t)

            self.queryset = self.queryset.filter(office_id=request.query_params.get('office')).annotate(
                suitable=Count('rooms__tables', filter=Q(rooms__type__title=request.query_params.get('room_type'))
                                                       &
                                                       Q(rooms__tables__in=tables_count))).prefetch_related('rooms')

            count = tables_count.count()
        else:
            try:
                room_type = RoomType.objects.get(office_id=request.query_params.get('office'),
                                                 title=request.query_params.get('room_type'))
            except RoomType.DoesNotExist:
                raise ResponseException("Room Type not found", status_code=status.HTTP_404_NOT_FOUND)

            if room_type.unified:
                self.queryset = self.queryset.filter(office_id=request.query_params.get('office')).annotate(
                    suitable=Count('rooms__tables', filter=Q(rooms__type__title=room_type.title)
                                                           &
                                                           Q(rooms__room_marker__isnull=False)
                                                           &
                                                           Q(rooms__tables__table_marker__isnull=True)
                                                           &
                                                           ~Q(rooms__tables__id__in=bookings))).prefetch_related(
                    'rooms')
            else:
                self.queryset = self.queryset.filter(office_id=request.query_params.get('office')).annotate(
                    suitable=Count('rooms__tables', filter=Q(rooms__type__title=room_type.title)
                                                           &
                                                           Q(rooms__tables__is_occupied=False)
                                                           &
                                                           Q(rooms__room_marker__isnull=False)
                                                           &
                                                           Q(rooms__tables__table_marker__isnull=False)
                                                           &
                                                           ~Q(rooms__tables__id__in=bookings))).prefetch_related(
                    'rooms')

        response = []

        for floor in self.queryset:
            response.append({
                "id": str(floor.id),
                "suitable": int(floor.suitable)
            })
            if not tag:
                count += int(floor.suitable)

        response = {
            'results': response,
            'count': count
        }

        return Response(response, status=status.HTTP_200_OK)




