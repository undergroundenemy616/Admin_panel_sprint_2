import os

import django_filters
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from exchangelib import Account as Ac, Credentials, Configuration, DELEGATE
from exchangelib.errors import UnauthorizedError, TransportError
from exchangelib.services import GetRooms
from rest_framework import filters, status, viewsets
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.response import Response

from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from rooms.filters_admin import AdminRoomFilter
from rooms.models import Room, RoomMarker
from rooms.serializers_admin import (AdminRoomListDeleteSerializer, AdminRoomSerializer,
                                     AdminRoomWithTablesSerializer, AdminRoomCreateUpdateSerializer,
                                     AdminRoomMarkerCreateSerializer, SwaggerRoomList,
                                     AdminRoomExchangeCreateSerializer)


@method_decorator(name='list', decorator=swagger_auto_schema(query_serializer=SwaggerRoomList))
class AdminRoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = AdminRoomFilter
    search_fields = ['title', 'type__title', 'description', 'zone__title', 'floor__title']
    serializer_class = AdminRoomSerializer
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination

    def get_queryset(self):
        self.queryset = self.queryset.select_related(
            'floor', 'type', 'zone', 'type', 'type__icon', 'room_marker').prefetch_related('images').annotate(
            capacity=Count('tables'),
            occupied=Count('tables', filter=Q(tables__is_occupied=True)),
            free=Count('tables', filter=Q(tables__is_occupied=False)))
        if self.request.query_params.get('tables') and self.request.method == "GET":
            self.queryset = self.queryset.prefetch_related('tables', 'tables__tags', 'tables__images',
                                                           'tables__table_marker', 'tables__tags__icon')
        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "GET" and self.request.query_params.get('tables', '').lower() == 'true':
            return AdminRoomWithTablesSerializer
        if self.request.method in ['POST', 'PUT']:
            return AdminRoomCreateUpdateSerializer
        return self.serializer_class


class AdminRoomListDeleteView(GenericAPIView):
    serializer_class = AdminRoomListDeleteSerializer
    permission_classes = (IsAdmin,)

    def delete(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminRoomMarkerViewSet(viewsets.ModelViewSet):
    queryset = RoomMarker.objects.all()
    serializer_class = AdminRoomMarkerCreateSerializer
    permission_classes = (IsAdmin, )


class AdminRoomExchangeView(CreateAPIView):
    serializer_class = AdminRoomExchangeCreateSerializer
    permission_classes = (IsAdmin, )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.create(validated_data=serializer.data)
        return Response(response, status=status.HTTP_201_CREATED)
