from datetime import datetime

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, UpdateModelMixin)
from rest_framework.response import Response
from rest_framework.filters import SearchFilter

from bookings.models import Booking
from bookings.serializers import (BookingActivateActionSerializer,
                                  BookingDeactivateActionSerializer,
                                  BookingFastSerializer, BookingListSerializer,
                                  BookingListTablesSerializer,
                                  BookingSerializer, BookingSlotsSerializer,
                                  BookListTableSerializer,
                                  SwaggerBookListActiveParametrs,
                                  SwaggerBookListTableParametrs, BookingPersonalSerializer)
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from tables.serializers import Table, TableSerializer


class BookingsView(GenericAPIView, CreateModelMixin, ListModelMixin):
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
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.account.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        # TODO: Add addition not required "?id=" parameter for user id
        return self.list(request, *args, **kwargs)


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


class BookingsActiveListView(BookingsView):
    queryset = Booking.objects.active_only().all()
    serializer_class = BookingListSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerBookListActiveParametrs)
    def get(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return self.list(request, *args, **kwargs)


class BookingsUserListView(BookingsAdminView):
    serializer_class = BookingListSerializer

    def get(self, request, *args, **kwargs):
        # request.data['user'] = request.user.id
        return self.list(request, *args, **kwargs)


class ActionCheckAvailableSlotsView(GenericAPIView):
    serializer_class = BookingSlotsSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActionActivateBookingsView(GenericAPIView):
    """
    Authenticated User route. Change status of booking.
    """
    serializer_class = BookingActivateActionSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # request.data['user'] = request.user
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionDeactivateBookingsView(GenericAPIView):
    """
    Admin route. Deactivates any booking
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionEndBookingsView(GenericAPIView):
    """
    User route. Deactivate booking only connected with User
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionCancelBookingsView(GenericAPIView, DestroyModelMixin):
    """
    User route. Delete booking object from DB
    """
    queryset = Booking.objects.all()

    def delete(self, request, pk=None, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=pk)
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return self.destroy(request, *args, **kwargs)


class CreateFastBookingsView(GenericAPIView):
    """
    Admin route. Fast booking for any user.
    """
    serializer_class = BookingFastSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
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
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerBookListTableParametrs)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('date_from') and request.query_params.get('date_to'):
            table_instance = get_object_or_404(Table, pk=request.query_params.get('table'))
            serializer = self.serializer_class(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            queryset = self.queryset.is_overflowed_with_data(table=table_instance.id,
                                                             date_from=serializer.data['date_from'],
                                                             date_to=serializer.data['date_to'])
            response = {
                'id': table_instance.id,
                'table': TableSerializer(instance=table_instance).data,
                'floor': table_instance.room.floor.title,
                'room': table_instance.room.title,
                'history': [BookingSerializer(instance=book).data for book in queryset]
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            table_instance = get_object_or_404(Table, pk=request.query_params.get('table'))
            queryset = self.queryset.filter(table=table_instance.id)
            response = {
                'id': table_instance.id,
                'table': TableSerializer(instance=table_instance).data,
                'floor': table_instance.room.floor.title,
                'room': table_instance.room.title,
                'history': [BookingSerializer(instance=book).data for book in queryset]
            }
            return Response(response, status=status.HTTP_200_OK)


class BookingListPersonalView(GenericAPIView, ListModelMixin):
    """
    All User route. Shows all bookings that User have.
    Can be filtered by: date,
    """
    serializer_class = BookingPersonalSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [SearchFilter, ]
    search_fields = ['table__title',
                     'table__room__title',
                     'table__room__type__title',
                     'table__room__floor__office__title',
                     'table__room__floor__office__description']
    pagination_class = DefaultPagination

    @swagger_auto_schema(query_serializer=BookingPersonalSerializer)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('search'):
            self.serializer_class = BookingSerializer
            return self.list(request, *args, **kwargs)
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        date_from = datetime.strptime(request.query_params.get('date_from'), '%Y-%m-%dT%H:%M:%S.%fZ')
        date_to = datetime.strptime(request.query_params.get('date_to'), '%Y-%m-%dT%H:%M:%S.%fZ')
        is_over = bool(serializer.data['is_over']) if serializer.data.get('is_over') else 0
        req_booking = self.queryset.filter(user=request.user.account.id) \
            .filter(
            Q(is_over=is_over),
            Q(date_from__gte=date_from, date_from__lt=date_to)
            | Q(date_from__lte=date_from, date_to__gte=date_to)
            | Q(date_to__gt=date_from, date_to__lte=date_to))
        self.queryset = req_booking
        self.serializer_class = BookingSerializer
        return self.list(request, *args, **kwargs)
