import orjson
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response

from bookings.filters_admin import AdminBookingFilter
from bookings.models import Booking
from bookings.serializers_admin import (AdminBookingCreateFastSerializer,
                                        AdminBookingSerializer,
                                        AdminSwaggerDashboard,
                                        AdminStatisticsSerializer, AdminBookingEmployeeStatisticsSerializer,
                                        AdminSwaggerBookingEmployee, AdminSwaggerBookingFuture,
                                        AdminBookingFutureStatisticsSerializer, AdminSwaggerRoomType,
                                        AdminBookingRoomTypeSerializer, AdminMeetingGroupBookingSerializer,
                                        AdminWorkplaceGroupBookingSerializer)
from core.handlers import ResponseException
from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from files.serializers_admin import AdminFileSerializer
from group_bookings.models import GroupBooking
from group_bookings.serializers_admin import AdminGroupBookingSerializer, AdminGroupWorkspaceSerializer
from users.models import Account
from users.serializers_admin import AdminUserSerializer


class AdminBookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin, )
    pagination_class = LimitStartPagination
    filterset_class = AdminBookingFilter

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.select_related('table', 'table__room', 'table__room__floor',
                                                         'table__room__floor__office',
                                                         'user')
        return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            if self.request.data.get('type') and not self.request.data.get('table'):
                return AdminBookingCreateFastSerializer
        return AdminBookingSerializer

    def list(self, request, *args, **kwargs):
        response = super(AdminBookingViewSet, self).list(request, *args, **kwargs).data
        if self.request.query_params.get('user'):
            response['user'] = AdminUserSerializer(instance=get_object_or_404(Account, pk=self.request.query_params.get('user'))).data
        return Response(response)


class AdminBookingStatisticsDashboardView(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=AdminSwaggerDashboard)
    def get(self, request, *args, **kwargs):
        serializer = AdminStatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        response = serializer.get_statistic()

        return Response(orjson.loads(orjson.dumps(response)), status=status.HTTP_200_OK)


class AdminBookingEmployeeStatisticsView(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=AdminSwaggerBookingEmployee)
    def get(self, request, *args, **kwargs):
        serializer = AdminBookingEmployeeStatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        response = serializer.get_statistic()

        return Response(data=AdminFileSerializer(instance=response).data, status=status.HTTP_200_OK)


class AdminBookingFutureStatisticsView(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=AdminSwaggerBookingFuture)
    def get(self, request, *args, **kwargs):
        serializer = AdminBookingFutureStatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        response = serializer.get_statistic()

        return Response(data=AdminFileSerializer(instance=response).data, status=status.HTTP_200_OK)


class AdminBookingRoomTypeStatisticsView(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=AdminSwaggerRoomType)
    def get(self, request, *args, **kwargs):
        serializer = AdminBookingRoomTypeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        response = serializer.get_statistic()

        return Response(data=AdminFileSerializer(instance=response).data, status=status.HTTP_200_OK)


class AdminGroupMeetingBookingViewSet(viewsets.ModelViewSet):
    queryset = GroupBooking.objects.all()
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.filter(Q(bookings__table__room__type__unified=True,
                                                   bookings__table__room__type__bookable=True,
                                                   bookings__table__room__type__is_deletable=False)).\
                prefetch_related('bookings', 'bookings__table',
                                 'bookings__table__room', 'bookings__table__room__room_marker',
                                 'bookings__table__room__type', 'bookings__table__room__floor',
                                 'bookings__table__room__floor__office', 'bookings__user').distinct()
        return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminMeetingGroupBookingSerializer
        return AdminGroupBookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = AdminMeetingGroupBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.group_create_meeting(context=self.request.parser_context)
        headers = self.get_success_headers(serializer.data)
        return Response(response, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        account = request.user.account
        if account == instance.author or account.user.is_staff:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ResponseException("You not allowed to perform this action", status_code=status.HTTP_403_FORBIDDEN)


class AdminGroupWorkplaceBookingViewSet(viewsets.ModelViewSet):
    queryset = GroupBooking.objects.all()
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.filter(Q(bookings__table__room__type__unified=False,
                                                   bookings__table__room__type__bookable=True,
                                                   bookings__table__room__type__is_deletable=False)).\
                prefetch_related('bookings', 'bookings__table',
                                 'bookings__table__room', 'bookings__table__room__room_marker',
                                 'bookings__table__room__type', 'bookings__table__room__floor',
                                 'bookings__table__room__floor__office', 'bookings__user').distinct()
        return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminWorkplaceGroupBookingSerializer
        return AdminGroupWorkspaceSerializer

    def create(self, request, *args, **kwargs):
        serializer = AdminWorkplaceGroupBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.group_create_workplace(context=self.request.parser_context)
        headers = self.get_success_headers(serializer.data)
        return Response(response, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        account = request.user.account
        if account == instance.author or account.user.is_staff:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ResponseException("You not allowed to perform this action", status_code=status.HTTP_403_FORBIDDEN)

