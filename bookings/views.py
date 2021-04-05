from datetime import datetime
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.response import Response


from bookings.models import Booking
from bookings.serializers import (BookingFastSerializer, BookingListSerializer,
                                  BookingListTablesSerializer,
                                  BookingPersonalSerializer, BookingSerializer,
                                  SwaggerBookListActiveParametrs,
                                  SwaggerBookListTableParametrs)
from core.pagination import LimitStartPagination
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from tables.serializers import Table, TableSerializer
from users.models import Account
from users.serializers import AccountSerializer


class BookingsView(GenericAPIView,
                   CreateModelMixin,
                   ListModelMixin,
                   DestroyModelMixin):
    """
    Book table, get information about specific booking.
    Methods available: GET, POST
    GET: Return information about one booking according to requested ID
     Params - :id:: booking id information about want to get
    POST: Create booking on requested table if it not overflowed
     Params - :date_from: - booking start datetime
              :date_to: - booking end datetime
              :table: - seat that need to be book
              :Theme: - Used only when booking table in room.room_type.unified=True, else used default value
    """
    serializer_class = BookingSerializer
    queryset = Booking.objects.all().select_related('table', 'table__room', 'table__table_marker',
                                                    'table__room__floor', 'table__room__floor__office',
                                                    'table__room__zone', 'table__room__type'
                                                    ).prefetch_related('user', 'table__tags', 'table__tags__icon',
                                                                       'table__images')
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):  # TODO CHECK maybe not work
        if self.request.method == 'DELETE':
            self.permission_classes = (IsAdmin, )
        return super(BookingsView, self).get_permissions()  # TODO: Not working

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.account.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        # TODO: Add addition not required "?id=" parameter for user id
        return self.list(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
        # TODO Check working and stability


class BookingsAdminView(BookingsView):
    """
    Admin route. Create Booking for any user.
    """
    permission_classes = (IsAdmin,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreateFastBookingsView(GenericAPIView):
    """
    Admin route. Fast booking for any user.
    """
    serializer_class = BookingFastSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.account.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FastBookingAdminView(CreateFastBookingsView):
    permission_classes = (IsAdmin,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingListTablesView(GenericAPIView, ListModelMixin):
    """
    All User route. Show booking history of any requested table.
    Can be filtered by date_from-date_to.
    """
    serializer_class = BookingListTablesSerializer
    queryset = Booking.objects.all().select_related('table', 'user').prefetch_related(
        'table__room__floor__office', 'table__room__type', 'table__room__zone', 'table__tags',
        'table__images', 'table__table_marker')
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerBookListTableParametrs)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('date_from') and request.query_params.get('date_to'):
            table_instance = get_object_or_404(Table, pk=request.query_params.get('table'))
            serializer = self.serializer_class(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            queryset = Booking.objects.is_overflowed_with_data(table=table_instance.id,
                                                               date_from=serializer.data['date_from'],
                                                               date_to=serializer.data['date_to']).select_related(
            'table', 'user', 'table__room', 'table__room__floor', 'table__room__type', 'table__room__zone',
            'table__room__floor__office', 'table__table_marker').prefetch_related('table__tags', 'table__images'
                                                                                  ).order_by('-date_from')
            response = {
                'id': table_instance.id,
                'table': TableSerializer(instance=table_instance).data,
                'floor': table_instance.room.floor.title,
                'room': table_instance.room.title,
                'history': BookingSerializer(instance=queryset, many=True).data
                # 'history': [BookingSerializer(instance=book).data for book in queryset]
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            table_instance = get_object_or_404(Table.objects.select_related('room', 'room__floor',
                'table_marker').prefetch_related('tags', 'images'), pk=request.query_params.get('table'))
            queryset = self.queryset.filter(table=table_instance.id).order_by('-date_from')
            response = {
                'id': table_instance.id,
                'table': TableSerializer(instance=table_instance).data,
                'floor': table_instance.room.floor.title,
                'room': table_instance.room.title,
                'history': BookingSerializer(instance=queryset, many=True).data
                # 'history': [BookingSerializer(instance=book).data for book in queryset]
            }
            return Response(response, status=status.HTTP_200_OK)


class BookingListPersonalView(GenericAPIView, ListModelMixin):
    """
    All User route. Shows all bookings that User have.
    Can be filtered by: date,
    """
    serializer_class = BookingPersonalSerializer
    queryset = Booking.objects.all().select_related('table', 'user').prefetch_related(
        'table__room__floor__office', 'table__room__type', 'table__room__zone', 'table__tags',
        'table__images', 'table__table_marker').order_by('-is_active', '-date_from')
    permission_classes = (IsAuthenticated,)
    filter_backends = [SearchFilter, ]
    search_fields = ['table__title',
                     'table__room__title',
                     'table__room__type__title',
                     'table__room__floor__office__title',
                     'table__room__floor__office__description']
    pagination_class = LimitStartPagination

    @swagger_auto_schema(query_serializer=BookingPersonalSerializer)
    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        date_from = request.query_params.get('date_from', datetime.min)
        date_to = request.query_params.get('date_to', datetime.max)
        is_over = bool(serializer.data['is_over']) if serializer.data.get('is_over') else 0
        if is_over == 1:
            req_booking = self.queryset.filter(user=request.user.account.id).filter(
                Q(status__in=['canceled', 'auto_canceled', 'over']),
                Q(date_from__gte=date_from, date_from__lt=date_to)
                | Q(date_from__lte=date_from, date_to__gte=date_to)
                | Q(date_to__gt=date_from, date_to__lte=date_to))
        else:
            req_booking = self.queryset.filter(user=request.user.account.id).filter(
                Q(status__in=['waiting', 'active']),
                Q(date_from__gte=date_from, date_from__lt=date_to)
                | Q(date_from__lte=date_from, date_to__gte=date_to)
                | Q(date_to__gt=date_from, date_to__lte=date_to))
        self.queryset = req_booking.order_by('-date_from')
        self.serializer_class = BookingSerializer
        return self.list(request, *args, **kwargs)


class BookingsListUserView(BookingsAdminView):
    serializer_class = BookingListSerializer
    queryset = Booking.objects.all().prefetch_related('user').select_related(
        'table', 'table__room', 'table__room__type', 'table__room__floor', 'table__room__floor__office')

    @swagger_auto_schema(query_serializer=SwaggerBookListActiveParametrs)
    def get(self, request, *args, **kwargs):
        account = get_object_or_404(Account, pk=request.query_params['user'])
        by_user = self.queryset.filter(user=account.id, status__in=['waiting', 'active'])
        self.queryset = by_user.order_by('-date_from')
        response = self.list(request, *args, **kwargs)
        response.data['user'] = AccountSerializer(instance=account).data
        return response

