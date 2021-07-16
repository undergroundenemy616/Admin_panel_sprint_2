import orjson
from django.db.models import Q
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.mixins import ListModelMixin
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
from group_bookings.serializers_admin import (AdminGroupBookingSerializer,
                                              AdminGroupWorkspaceSerializer,
                                              AdminGroupCombinedSerializer)
from group_bookings.serializers_mobile import MobileGroupBookingSerializer
from users.models import Account
from users.serializers_admin import AdminUserSerializer


class AdminBookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().order_by('-date_from')
    permission_classes = (IsAdmin, )
    pagination_class = LimitStartPagination
    filterset_class = AdminBookingFilter

    def get_queryset(self):
        if self.request.method == "GET":
            if str(self.request.query_params.get('group')).lower() == 'true':
                self.queryset = self.queryset.filter(~Q(group_booking_id=None)).select_related('table',
                                                                                               'table__room',
                                                                                               'table__room__floor',
                                                                                               'table__room__floor__office',
                                                                                               'user')
            else:
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
        serializer = AdminBookingEmployeeStatisticsSerializer(data=request.query_params, context=request)
        serializer.is_valid(raise_exception=True)
        response = serializer.get_statistic()

        return Response(data=AdminFileSerializer(instance=response).data, status=status.HTTP_200_OK)


class AdminBookingFutureStatisticsView(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=AdminSwaggerBookingFuture)
    def get(self, request, *args, **kwargs):
        serializer = AdminBookingFutureStatisticsSerializer(data=request.query_params, context=request)
        serializer.is_valid(raise_exception=True)
        response = serializer.get_statistic()

        return Response(data=AdminFileSerializer(instance=response).data, status=status.HTTP_200_OK)


class AdminBookingRoomTypeStatisticsView(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=AdminSwaggerRoomType)
    def get(self, request, *args, **kwargs):
        serializer = AdminBookingRoomTypeSerializer(data=request.query_params, context=request)
        serializer.is_valid(raise_exception=True)
        response = serializer.get_statistic()

        return Response(data=AdminFileSerializer(instance=response).data, status=status.HTTP_200_OK)


class AdminGroupMeetingBookingViewSet(viewsets.ModelViewSet):
    queryset = GroupBooking.objects.all()
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination
    serializer_class = AdminGroupBookingSerializer

    def get_queryset(self):
        if self.request.method == "GET":
            if self.request.query_params.get('user'):
                self.queryset = self.queryset.filter(Q(bookings__table__room__type__unified=True,
                                                       bookings__table__room__type__bookable=True,
                                                       bookings__table__room__type__is_deletable=False)
                                                     &
                                                     (Q(author_id=self.request.query_params.get('user'))
                                                      |
                                                      Q(bookings__user_id=self.request.query_params.get('user')))).\
                    prefetch_related('bookings', 'bookings__table',
                                     'bookings__table__room', 'bookings__table__room__room_marker',
                                     'bookings__table__room__type', 'bookings__table__room__floor',
                                     'bookings__table__room__floor__office', 'bookings__user').distinct()
            else:
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
        if account == instance.author or account.user.is_staff:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ResponseException("You not allowed to perform this action", status_code=status.HTTP_403_FORBIDDEN)

    def list(self, request, *args, **kwargs):
        response = super(AdminGroupMeetingBookingViewSet, self).list(request, *args, **kwargs).data
        if self.request.query_params.get('user'):
            response['user'] = AdminUserSerializer(instance=get_object_or_404(Account, pk=self.request.query_params.get('user'))).data
        return Response(response)


class AdminGroupWorkplaceBookingViewSet(viewsets.ModelViewSet):
    queryset = GroupBooking.objects.all()
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination
    serializer_class = AdminGroupWorkspaceSerializer

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
        if account == instance.author or account.user.is_staff:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ResponseException("You not allowed to perform this action", status_code=status.HTTP_403_FORBIDDEN)


class AdminGroupCombinedBookingSerializer(GenericAPIView,
                                          ListModelMixin):
    queryset = GroupBooking.objects.all().prefetch_related('bookings', 'bookings__table', 'bookings__table__room',
                                                           'bookings__table__room__floor',
                                                           'bookings__table__room__floor__office',
                                                           'bookings__table__room__room_marker',
                                                           'bookings__user')
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination
    serializer_class = AdminGroupCombinedSerializer
    filter_backends = [SearchFilter]
    search_fields = ['bookings__user__first_name', 'bookings__user__last_name', 'bookings__user__email',
                     'bookings__user__phone_number', 'author__email', 'author__first_name', 'author__last_name',
                     'author__phone_number']

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.query_params.get('user'):
            queryset = queryset.filter(bookings__user_id=request.query_params.get('user'))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdminGroupCombinedSerializer(instance=queryset, data=request.query_params, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

