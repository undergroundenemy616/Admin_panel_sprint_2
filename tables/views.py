import orjson, decimal
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, Response,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   status)

from bookings.models import Booking
from bookings.serializers import BookingSerializer, BookingSerializerForTableSlots
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from offices.models import Office
from tables.models import Rating, Table, TableTag,  TableMarker
from tables.serializers import (BaseTableTagSerializer, CreateTableSerializer,
                                TableMarkerSerializer, TableSlotsSerializer,
                                SwaggerTableParameters, SwaggerTableTagParametrs,
                                TableSerializer, TableTagSerializer,
                                UpdateTableSerializer, UpdateTableTagSerializer,
                                SwaggerTableSlotsParametrs, basic_table_serializer)


class TableView(ListModelMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerTableParameters)
    def get(self, request, *args, **kwargs):
        response = []
        tables = self.queryset.all()

        if request.query_params.get('office'):
            tables = tables.filter(room__floor__office_id=request.query_params.get('office'))
        if request.query_params.get('floor'):
            tables = tables.filter(room__floor_id=request.query_params.get('floor'))
        if request.query_params.get('room'):
            tables = tables.filter(room_id=request.query_params.get('room'))
        if request.query_params.get('free'):
            if int(request.query_params.get('free')) == 1:
                tables = tables.filter(is_occupied=False)
            elif int(request.query_params.get('free')) == 0:
                tables = tables.filter(is_occupied=True)

        for table in tables:
            response.append(basic_table_serializer(table=table))

        if request.query_params.getlist('tags'):
            tables_with_the_right_tags = []

            for table in response:
                for tag in table['tags']:
                    if tag['title'] in request.query_params.getlist('tags'):
                        tables_with_the_right_tags.append(table)

            response = list({r['id']: r for r in tables_with_the_right_tags}.values())

        ratings = Rating.objects.all()
        for table in response:
            table['ratings'] = ratings.filter(table_id=table['id']).count()

        response_dict = {
            'results': response
        }
        return Response(orjson.loads(orjson.dumps(response_dict, default=default)), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        self.serializer_class = CreateTableSerializer
        return self.create(request, *args, **kwargs)


class DetailTableView(RetrieveModelMixin,
                      UpdateModelMixin,
                      DestroyModelMixin,
                      GenericAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    permission_classes = (IsAuthenticated, )

    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateTableSerializer
        # return TableSerializer(instance=Table.objects.get(id=))
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # self.permission_classes = (IsAuthenticated, )
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class TableTagView(ListModelMixin,
                   CreateModelMixin,
                   GenericAPIView):
    serializer_class = TableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = None
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(query_serializer=SwaggerTableTagParametrs)
    def get(self, request, *args, **kwargs):
        # self.serializer_class = ListTableTagSerializer
        # serializer = self.serializer_class(data={'office': request.query_params.get('office')})
        # serializer.is_valid(raise_exception=True)
        self.serializer_class = BaseTableTagSerializer
        self.queryset = TableTag.objects.filter(office_id=get_object_or_404(Office,
                                                                            pk=request.query_params.get('office')))
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        if isinstance(request.data['title'], str):
            request.data['title'] = [request.data['title']]
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_tag = serializer.save()
        return Response(serializer.to_representation(instance=created_tag),
                        status=status.HTTP_201_CREATED)


class DetailTableTagView(GenericAPIView,
                         UpdateModelMixin,
                         DestroyModelMixin):
    serializer_class = TableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAdmin, )

    def put(self, request, pk=None, *args, **kwargs):
        print(2)
        instance = get_object_or_404(TableTag, pk=pk)
        self.serializer_class = UpdateTableTagSerializer
        serializer = self.serializer_class(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        response = serializer.to_representation(updated)
        return Response(response[0], status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class TableMarkerView(CreateModelMixin, DestroyModelMixin,
                      GenericAPIView):

    queryset = TableMarker.objects.all()
    serializer_class = TableMarkerSerializer
    permission_classes = (IsAdmin, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        table_serializer = TableSerializer(instance=instance.table)
        return Response(table_serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        print(3)
        table = get_object_or_404(Table, pk=request.data['table'])
        if hasattr(table, 'table_marker'):
            serializer = self.serializer_class(data=request.data,
                                               instance=TableMarker.objects.get(pk=table.table_marker.id))
        else:
            return Response({"message": "Table doesn't have marker"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        table_serializer = TableSerializer(instance=instance.table)
        return Response(table_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'table': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        }
    ))
    def delete(self, request, *args, **kwargs):
        table = get_object_or_404(Table, pk=request.data['table'])
        if not hasattr(table, 'table_marker'):
            return Response({"message": "table doesn't have marker"}, status=status.HTTP_400_BAD_REQUEST)
        instance = get_object_or_404(TableMarker, pk=table.table_marker.id)
        instance.delete()
        table.refresh_from_db()
        return Response(TableSerializer(instance=table).data, status=status.HTTP_200_OK)


class TableSlotsView(ListModelMixin,
                     CreateModelMixin,
                     GenericAPIView):
    serializer_class = TableSlotsSerializer
    queryset = Table.objects.all()
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
            date = datetime.strptime(request.query_params.get('date'), '%Y-%m-%d')
            if request.query_params.get('monthly'):
                if int(request.query_params.get('monthly')) == 1:
                    for booking in bookings:
                        if booking.date_from.year == date.year == booking.date_to.year:
                            if booking.date_from.month == date.month == booking.date_to.month:
                                occupied.append(booking)
                return Response(BookingSerializerForTableSlots(instance=occupied, many=True).data, status=status.HTTP_200_OK)
            elif request.query_params.get('daily'):
                if int(request.query_params.get('daily')) == 1:
                    for booking in bookings:
                        if booking.date_from.date() <= date.date() <= booking.date_to.date():
                            occupied.append(booking)
                return Response(BookingSerializerForTableSlots(instance=occupied, many=True).data, status=status.HTTP_200_OK)
            else:
                return Response("Please, select filter", status.HTTP_400_BAD_REQUEST)
        else:
            return Response(BookingSerializerForTableSlots(instance=bookings, many=True).data, status=status.HTTP_200_OK)


def default(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    raise TypeError
