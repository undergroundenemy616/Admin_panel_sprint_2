from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from core.pagination import DefaultPagination
from bookings.models import Booking
from bookings.serializers import BookingSerializer, BookingSlotsSerializer, BookingListSerializer


class BookingsView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination

    def post(self, request, *args, **kwargs):
        # TODO: Waiting for auth
        # request.data['user'] = request.user.id
        request.data['user'] = '05f0c55c-f890-4833-8f95-7a3054e7edcb'
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        # TODO: Add addition not required "?id=" parameter for user id
        return self.list(request, *args, **kwargs)


class BookingsAdminView(BookingsView):
    # permission_classes = (IsAdminUser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingsActiveListView(BookingsView):
    queryset = Booking.objects.active_only().all()
    serializer_class = BookingListSerializer

    def get(self, request, *args, **kwargs):
        # TODO: Waiting for auth
        # request.data['user'] = request.user.id
        request.data['user'] = '05f0c55c-f890-4833-8f95-7a3054e7edcb'
        return self.list(request, *args, **kwargs)


class BookingsUserListView(BookingsAdminView):
    serializer_class = BookingListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ActionCheckAvailableSlotsView(GenericAPIView):
    serializer_class = BookingSlotsSerializer
    queryset = Booking.objects.all()

    def post(self, request, *args, **kwargs):
        # TODO: Waiting for auth
        # request.data['user'] = request.user.id
        request.data['user'] = '05f0c55c-f890-4833-8f95-7a3054e7edcb'
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActionActivateBookingsView(GenericAPIView):
    pass


class ActionDeactivateBookingsView(GenericAPIView):
    pass


class ActionEndBookingsView(GenericAPIView):
    pass
