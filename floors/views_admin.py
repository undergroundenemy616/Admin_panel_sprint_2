from rest_framework import viewsets, status
from rest_framework.response import Response

from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from floors.filters_admin import AdminFloorFilter
from floors.models import Floor, FloorMap
from floors.serializers_admin import (AdminFloorSerializer,
                                      AdminSingleFloorSerializer, AdminFloorMapSerializer,
                                      AdminCreateUpdateFloorMapSerializer, AdminFloorClearValidation)


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

    def clear_floor(self, request, *args, **kwargs):
        AdminFloorClearValidation(data=request.data).is_valid(raise_exception=True)
        instance = self.queryset.get(pk=request.data.get('floor'))
        for room in instance.rooms.all():
            if hasattr(room, 'room_marker'):
                room.room_marker.delete()
        return Response(data=self.serializer_class(instance=instance).data, status=status.HTTP_200_OK)


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
