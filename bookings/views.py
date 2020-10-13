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
    BookingDeactivateActionSerializer, BookingFastSerializer, BookingAdminSerializer


class BookingsView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination

    def post(self, request, *args, **kwargs):
        # request.data['user'] = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class BookingsAdminView(BookingsView):
    serializer_class = BookingAdminSerializer
    permission_classes = (IsAdminUser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
    pass


class CreateFastBookingsView(GenericAPIView):
    serializer_class = BookingFastSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        # headers = self.get_success_headers()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
