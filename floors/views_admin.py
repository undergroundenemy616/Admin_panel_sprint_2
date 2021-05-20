from rest_framework import viewsets

from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from floors.filters_admin import AdminFloorFilter
from floors.models import Floor, FloorMap
from floors.serializers_admin import (AdminFloorSerializer,
                                      AdminSingleFloorSerializer, AdminFloorMapSerializer,
                                      AdminCreateUpdateFloorMapSerializer)


class AdminFloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    permission_classes = (IsAdmin, )
    serializer_class = AdminSingleFloorSerializer
    pagination_class = LimitStartPagination
    filterset_class = AdminFloorFilter

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.prefetch_related('floormap', 'floormap__image')
            return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminFloorSerializer
        return self.serializer_class


class AdminFloorMapViewSet(viewsets.ModelViewSet):
    queryset = FloorMap.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = AdminFloorMapSerializer
    pagination_class = LimitStartPagination

    def get_queryset(self):
        return self.queryset.select_related('image')

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT']:
            return AdminCreateUpdateFloorMapSerializer
        return self.serializer_class
