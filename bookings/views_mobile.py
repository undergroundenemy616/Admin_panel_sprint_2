import datetime

from django.db.models import Q
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, ListModelMixin, DestroyModelMixin
from rest_framework.response import Response

from bookings.models import Booking, JobStore
from bookings.serializers import BookingPersonalSerializer
from bookings.serializers_mobile import (
    MobileBookingActivateActionSerializer,
    MobileBookingDeactivateActionSerializer, MobileBookingSerializer, MobileMeetingGroupBookingSerializer,
    MobileWorkplaceGroupBookingSerializer)
from core.pagination import DefaultPagination, LimitStartPagination
from core.permissions import IsAuthenticated
from group_bookings.models import GroupBooking
from group_bookings.serializers_mobile import MobileGroupBookingSerializer, MobileGroupWorkspaceSerializer


class MobileBookingsView(GenericAPIView,
                         CreateModelMixin,
                         DestroyModelMixin):
    serializer_class = MobileBookingSerializer
    queryset = Booking.objects.all().select_related('table', 'table__room', 'table__table_marker',
                                                    'table__room__floor', 'table__room__floor__office',
                                                    'table__room__zone', 'table__room__type', 'user'
                                                    ).prefetch_related('table__tags', 'table__tags__icon',
                                                                       'table__images').order_by('-date_from')
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.account.id
        serializer = self.serializer_class(data=request.data, context=request)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MobileBookingListPersonalView(GenericAPIView, ListModelMixin):
    serializer_class = BookingPersonalSerializer
    queryset = Booking.objects.all().select_related('table', 'user', 'table__room__floor__office',
                                                    'table__room__type', 'table__room__zone',
                                                    'table__table_marker', 'group_booking',
                                                    'group_booking__author', 'table__room__floor'). \
        prefetch_related('table__tags', 'table__images').order_by('-date_from', 'id')
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
                Q(status__in=['auto_over', 'over']))
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
        if instance.status == 'waiting':
            instance.delete()
            return HttpResponse(status=204)
        elif instance.status == 'active':
            flag = {'status': 'over'}
            instance.set_booking_over(kwargs=flag)
            return Response(data={"result": "Booking is over"}, status=status.HTTP_200_OK)
        else:
            return Response(data={"result": "Booking already is over"}, status=status.HTTP_200_OK)


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
    permission_classes = (IsAuthenticated,)

    def delete(self, request, pk=None, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=pk)
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        request.data['booking'] = existing_booking.id
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)


class MobileGroupMeetingBookingViewSet(viewsets.ModelViewSet):
    queryset = GroupBooking.objects.all()
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitStartPagination
    serializer_class = MobileGroupBookingSerializer

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.filter(Q(bookings__table__room__type__unified=True,
                                                   bookings__table__room__type__bookable=True,
                                                   bookings__table__room__type__is_deletable=False)). \
                prefetch_related('bookings', 'bookings__table',
                                 'bookings__table__room', 'bookings__table__room__room_marker',
                                 'bookings__table__room__type', 'bookings__table__room__floor',
                                 'bookings__table__room__floor__office', 'bookings__user').distinct()
        return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MobileMeetingGroupBookingSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.group_create_meeting(context=self.request.parser_context)
        headers = self.get_success_headers(serializer.data)
        return Response(response, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        account = request.user.account
        if account == instance.author:
            if instance.bookings.filter(user=instance.author)[0].status != 'waiting':
                for booking in instance.bookings.all():
                    if booking.user.id == account.id:
                        pass
                    else:
                        booking.make_booking_over()
                last_author_booking = instance.bookings.filter(user=account.id)
                for last_booking in last_author_booking:
                    last_booking.make_booking_over()
                return Response(status=status.HTTP_200_OK)
            JobStore.objects.create(job_id='exchange_booking_cancel_' + str(instance.id),
                                    time_execute=datetime.datetime.now())
            for booking in instance.bookings.all():
                if booking.user.id == account.id:
                    pass
                else:
                    booking.make_booking_over()
            last_author_booking = instance.bookings.filter(user=account.id)
            for last_booking in last_author_booking:
                last_booking.make_booking_over()
            self.perform_destroy(instance)
            return HttpResponse(status=204)
        else:
            personal_booking = instance.bookings.get(user=request.user.account)
            if personal_booking.status != 'waiting':
                personal_booking.make_booking_over()
                return Response(status=status.HTTP_200_OK)
            personal_booking.delete()
            return HttpResponse(status=204)


class MobileGroupWorkplaceBookingViewSet(viewsets.ModelViewSet):
    queryset = GroupBooking.objects.all()
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitStartPagination
    serializer_class = MobileGroupWorkspaceSerializer

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.filter(Q(bookings__table__room__type__unified=False,
                                                   bookings__table__room__type__bookable=True,
                                                   bookings__table__room__type__is_deletable=False)). \
                prefetch_related('bookings', 'bookings__table',
                                 'bookings__table__room', 'bookings__table__room__room_marker',
                                 'bookings__table__room__type', 'bookings__table__room__floor',
                                 'bookings__table__room__floor__office', 'bookings__user').distinct()
        return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MobileWorkplaceGroupBookingSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.group_create_workplace(context=self.request.parser_context)
        headers = self.get_success_headers(serializer.data)
        return Response(response, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        account = request.user.account
        if account == instance.author:
            if instance.bookings.filter(user=instance.author)[0].status != 'waiting':
                for booking in instance.bookings.all():
                    booking.make_booking_over()
                return Response(status=status.HTTP_200_OK)
            self.perform_destroy(instance)
            return HttpResponse(status=204)
        else:
            personal_booking = instance.bookings.get(user=request.user.account)
            if personal_booking.status != 'waiting':
                personal_booking.make_booking_over()
                return Response(status=status.HTTP_200_OK)
            personal_booking.delete()
            return HttpResponse(status=204)
