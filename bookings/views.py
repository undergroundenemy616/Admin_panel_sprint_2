from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.response import Response

from core.permissions import IsAdmin, IsAuthenticated
from core.pagination import DefaultPagination
from bookings.models import Booking
from bookings.serializers import BookingSerializer, \
    BookingSlotsSerializer, \
    BookingActivateActionSerializer, \
    BookingDeactivateActionSerializer, BookingFastSerializer, \
    BookingListSerializer, BookingListTablesSerializer, TableSerializer


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
    pagination_class = None
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if request.query_params.get('date_from') and request.query_params.get('date_to'):
            serializer = self.serializer_class(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            queryset = self.queryset.filter(table=request.query_params.get('table'), date_from=request.query_params.get('date_from'),
                                            date_to=request.query_params.get('date_to'))
        else:
            self.serializer_class = TableSerializer
            serializer = self.serializer_class(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            queryset = self.queryset.filter(table=serializer.data['table'])
        return self.list(request, *args, **kwargs)


class BookingListPersonalView(GenericAPIView, ListModelMixin):
    """
    All User route. Shows all bookings that User have.
    Can be filtered by: date,
    """
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
