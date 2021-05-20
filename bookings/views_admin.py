from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from bookings.filters_admin import AdminBookingFilter
from bookings.models import Booking
from bookings.serializers_admin import (AdminBookingCreateFastSerializer,
                                        AdminBookingCreateSerializer,
                                        AdminBookingSerializer,
                                        AdminDetailUserForBookSerializer)
from core.handlers import ResponseException
from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from users.models import Account


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
            raise ResponseException("Takes only type or table parameter", status_code=status.HTTP_400_BAD_REQUEST)
        return AdminBookingSerializer

    def list(self, request, *args, **kwargs):
        response = super(AdminBookingViewSet, self).list(request, *args, **kwargs).data
        if self.request.query_params.get('user'):
            response['user'] = AdminDetailUserForBookSerializer(instance=get_object_or_404(Account, pk=self.request.query_params.get('user'))).data
        return Response(response)
