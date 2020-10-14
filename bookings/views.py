from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from backends.pagination import DefaultPagination
from bookings.models import Booking
from bookings.serializers import BookingSerializer, BookingSlotsSerializer


class BookingsView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class BookingsAdminView(BookingsView):
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
        request.data['user'] = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.instance, status=status.HTTP_200_OK)



class ActionActivateBookingsView(GenericAPIView):
    pass


class ActionDeactivateBookingsView(GenericAPIView):
    pass


class ActionEndBookingsView(GenericAPIView):
    pass
