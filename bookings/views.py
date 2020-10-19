from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from backends.pagination import DefaultPagination
from bookings.models import Booking
from bookings.serializers import BookingSerializer, \
    BookingSlotsSerializer, \
    BookingActivateActionSerializer, \
    BookingDeactivateActionSerializer, BookingFastSerializer


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

    def post(self, request, *args, **kwargs):
        # Get information about user,
        # made for reuse one serializer in admin booking, where field user requested
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class BookingsAdminView(BookingsView):
    """
    Admin route. Create Booking for any user.
    """

    # permission_classes = (IsAdminUser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.instance, status=status.HTTP_201_CREATED, headers=headers)


class ActionCheckAvailableSlotsView(GenericAPIView):
    serializer_class = BookingSlotsSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        # request.data['user'] = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.instance, status=status.HTTP_200_OK)


class ActionActivateBookingsView(GenericAPIView):
    """
    Authenticated User route. Change status of booking.
    """
    serializer_class = BookingActivateActionSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        # request.data['user'] = request.user
        get_id = get_object_or_404(Booking, pk=request.data.get('booking'))
        booking = Booking.objects.filter(id=get_id.id).first()
        serializer = self.serializer_class(data=request.data, instance=booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.to_representation(booking), status=status.HTTP_200_OK)


class ActionDeactivateBookingsView(GenericAPIView):
    """
    Admin route. Deactivates any booking
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        get_id = get_object_or_404(Booking, pk=request.data.get('booking'))
        booking = Booking.objects.filter(id=get_id.id).first()
        serializer = self.serializer_class(data=request.data, instance=booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.to_representation(booking), status=status.HTTP_200_OK)


class ActionEndBookingsView(GenericAPIView):
    """
    User route. Deactivate booking only connected with User
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.id:
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

    def delete(self, pk, request, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=pk)
        if existing_booking.user.id != request.user.id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return self.destroy(request, *args, **kwargs)


class CreateFastBookingsView(GenericAPIView):
    """
    Admin route. Fast booking for any user.
    """
    serializer_class = BookingFastSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FastBookingAdminView(CreateFastBookingsView):
    # permission_classes = [IsAdminUser, ]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.instance, status=status.HTTP_201_CREATED, headers=headers)


class BookingListTablesView(GenericAPIView):
    """
    All User route. Show booking history of any requested table.
    Can be filtered by date_from-date_to.
    """
    pass


class BookingListPersonalView(GenericAPIView):
    """
    All User route. Shows all bookings that User have.
    Can be filtered by: date,
    """
    pass
