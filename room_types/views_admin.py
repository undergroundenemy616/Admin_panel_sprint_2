from rest_framework import viewsets

from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from room_types.filters_admin import AdminRoomTypeFilter
from room_types.models import RoomType
from room_types.serializers_admin import (
    AdminRoomTypeSerializer, AdminRoomTypeCreateSerializer)


class AdminRoomTypeViewSet(viewsets.ModelViewSet):
    queryset = RoomType.objects.all()
    serializer_class = AdminRoomTypeSerializer
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination
    filterset_class = AdminRoomTypeFilter

    def get_queryset(self):
        return self.queryset.select_related('icon').prefetch_related('rooms__tables')

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminRoomTypeCreateSerializer
        return self.serializer_class
