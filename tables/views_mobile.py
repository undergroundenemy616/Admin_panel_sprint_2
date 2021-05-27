from datetime import datetime

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

from bookings.models import Booking
from bookings.serializers_mobile import MobileBookingSerializerForTableSlots
from core.pagination import DefaultPagination
from core.permissions import IsAdminOrReadOnly, IsAuthenticated
from offices.models import Office
from tables.models import Table, TableTag
from tables.serializers import (SwaggerTableSlotsParametrs,
                                SwaggerTableTagParametrs)
from tables.serializers_mobile import (MobileBaseTableTagSerializer,
                                       MobileTableSlotsSerializer,
                                       MobileTableTagSerializer,
                                       MobileDetailedTableSerializer)


class MobileTableTagView(ListModelMixin,
                         GenericAPIView):
    serializer_class = MobileTableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = None
    permission_classes = (IsAdminOrReadOnly, )

    @swagger_auto_schema(query_serializer=SwaggerTableTagParametrs)
    def get(self, request, *args, **kwargs):
        self.serializer_class = MobileBaseTableTagSerializer
        self.queryset = TableTag.objects.filter(office_id=get_object_or_404(Office,
                                                                            pk=request.query_params.get('office'))
                                                ).select_related('office', 'icon').prefetch_related('office__images')
        return self.list(request, *args, **kwargs)


class MobileTableSlotsView(ListModelMixin,
                           GenericAPIView):
    serializer_class = MobileTableSlotsSerializer
    queryset = Table.objects.all().prefetch_related('tags', 'images').select_related('table_marker')
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerTableSlotsParametrs)
    def get(self, request, pk=None, *args, **kwargs):
        try:
            self.queryset.get(id=pk)
        except Table.DoesNotExist:
            return Response("Table not found", status.HTTP_404_NOT_FOUND)

        bookings = Booking.objects.filter(table_id=pk)

        if request.query_params.get('date'):
            occupied = []
            try:
                date = datetime.strptime(request.query_params.get('date'), '%Y-%m-%d')
            except Exception as e:
                request_date = request.query_params.get('date')
                date = datetime.strptime(request_date.replace(' ', ''), '%Y-%m-%d')
            if request.query_params.get('monthly'):
                if int(request.query_params.get('monthly')) == 1:
                    for booking in bookings:
                        if booking.date_from.year == date.year == booking.date_to.year:
                            if booking.date_from.month == date.month == booking.date_to.month:
                                occupied.append(booking)
                return Response(MobileBookingSerializerForTableSlots(instance=occupied, many=True).data,
                                status=status.HTTP_200_OK)
            elif request.query_params.get('daily'):
                if int(request.query_params.get('daily')) == 1:
                    for booking in bookings:
                        if booking.date_from.date() <= date.date() <= booking.date_to.date() and \
                                booking.status in ['active', 'waiting']:
                            occupied.append(booking)
                return Response(MobileBookingSerializerForTableSlots(instance=occupied, many=True).data,
                                status=status.HTTP_200_OK)
            else:
                return Response("Please, select filter", status.HTTP_400_BAD_REQUEST)
        else:
            return Response(MobileBookingSerializerForTableSlots(instance=bookings, many=True).data,
                            status=status.HTTP_200_OK)


class MobileTableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = MobileDetailedTableSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.select_related(
                'table_marker', 'room',
                'room__floor', 'room__floor__office').prefetch_related('images', 'tags')
        return self.queryset
