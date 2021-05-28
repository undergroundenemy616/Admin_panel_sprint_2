import orjson
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response

from bookings.filters_admin import AdminBookingFilter
from bookings.models import Booking
from bookings.serializers_admin import (AdminBookingCreateFastSerializer,
                                        AdminBookingCreateSerializer,
                                        AdminBookingSerializer,
                                        AdminSwaggerDashboard,
                                        AdminStatisticsSerializer, AdminBookingEmployeeStatisticsSerializer,
                                        AdminSwaggerBookingEmployee, AdminSwaggerBookingFuture,
                                        AdminBookingFutureStatisticsSerializer, AdminSwaggerRoomType,
                                        AdminBookingRoomTypeSerializer)
from core.handlers import ResponseException
from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from files.serializers_admin import AdminFileSerializer
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
            elif self.request.data.get('table') and not self.request.data.get('type'):
                return AdminBookingCreateSerializer
            # raise ResponseException("Takes only type or table parameter", status_code=status.HTTP_400_BAD_REQUEST)
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
