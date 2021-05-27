from django.db.models import Q
from django.utils.timezone import now
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.response import Response

from bookings.models import Booking
from bookings.serializers import BookingPersonalSerializer
from bookings.serializers_mobile import (
    MobileBookingActivateActionSerializer,
    MobileBookingDeactivateActionSerializer, MobileBookingSerializer)
from core.pagination import DefaultPagination, LimitStartPagination
from core.permissions import IsAuthenticated


class MobileBookingsView(GenericAPIView,
                         CreateModelMixin,
                         ListModelMixin):
    serializer_class = MobileBookingSerializer
    queryset = Booking.objects.all().select_related('table', 'table__room', 'table__table_marker',
                                                    'table__room__floor', 'table__room__floor__office',
                                                    'table__room__zone', 'table__room__type'
                                                    ).prefetch_related('user', 'table__tags', 'table__tags__icon',
                                                                       'table__images')
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.account.id
        serializer = self.serializer_class(data=request.data, context=request)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class MobileBookingListPersonalView(GenericAPIView, ListModelMixin):
    serializer_class = BookingPersonalSerializer
    queryset = Booking.objects.all().select_related('table', 'user').prefetch_related(
        'table__room__floor__office', 'table__room__type', 'table__room__zone', 'table__tags',
        'table__images', 'table__table_marker').order_by('-date_from', 'id')
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
        time = serializer.data.get('time')
        if time == 'past':
            req_booking = self.queryset.filter(user=request.user.account.id).filter(
                Q(status__in=['canceled', 'early_end', 'over']))
        elif time == 'future':
            req_booking = self.queryset.filter(user=request.user.account.id).filter(
                Q(status__in=['waiting', 'active']))
        else:
            req_booking = self.queryset.filter(user=request.user.account.id)
        self.queryset = req_booking
        self.serializer_class = MobileBookingSerializer
        return self.list(request, *args, **kwargs)


class MobileCancelBooking(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def put(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Booking, pk=pk)
        now_date = now()
        if now_date < instance.date_activate_until and instance.status != 'active':
            instance.delete()
            return Response(data={"result": "Booking is deleted"}, status=status.HTTP_204_NO_CONTENT)
        flag = {'status': 'over'}
        instance.set_booking_over(kwargs=flag)
        return Response(data={"result": "Booking is over"}, status=status.HTTP_200_OK)


class MobileActionActivateBookingsView(GenericAPIView):
    serializer_class = MobileBookingActivateActionSerializer
    queryset = Booking.objects.all().select_related('table')
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class MobileActionCancelBookingsView(GenericAPIView):
    queryset = Booking.objects.all().select_related('table', 'user')
    serializer_class = MobileBookingDeactivateActionSerializer
    permission_classes = (IsAuthenticated, )

    def delete(self, request, pk=None, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=pk)
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        request.data['booking'] = existing_booking.id
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)