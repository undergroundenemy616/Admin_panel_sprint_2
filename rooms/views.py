from typing import Dict, Optional

from django.db.models import Q
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from core.pagination import DefaultPagination
from core.mixins import FilterListMixin
from rooms.models import Room, RoomMarker
from rooms.serializers import RoomSerializer, FilterRoomSerializer, CreateRoomSerializer, UpdateRoomSerializer, \
    RoomMarkerSerializer


class RoomsView(FilterListMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    pagination_class = DefaultPagination

    # permission_classes = (IsAdminUser,)

    @staticmethod
    def get_mapped_query(request: Request) -> Optional[Dict]:
        """Returns mapped literals for search in database or None."""
        serializer = FilterRoomSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query_params = serializer.data
        mapped = {"floor_id__in": query_params.get('floor'),
                  "floor__office_id": query_params.get('office'),
                  "type__title__in": query_params.get('type'),
                  "tables__tags__title__in": query_params.get('tags'),
                  "zone_id__in": query_params.get('zone'),
                  }
        items = []
        for field in mapped.keys():
            if not mapped[field]:
                items.append(field)
        for item in items:
            del mapped[item]
        return mapped

    def get(self, request, *args, **kwargs):
        if request.query_params.get('search'):
            self.queryset = Room.objects.filter(Q(title__icontains=request.query_params.get('search'))
                                                | Q(type__title__icontains=request.query_params.get('search'))
                                                | Q(description__icontains=request.query_params.get('search')))
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.serializer_class = CreateRoomSerializer
        return self.create(request, *args, **kwargs)


class DetailRoomView(RetrieveModelMixin,
                     UpdateModelMixin,
                     DestroyModelMixin,
                     GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    pagination_class = DefaultPagination

    # permission_classes = (IsAdminUser,)

    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateRoomSerializer
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RoomMarkerView(CreateModelMixin,
                     DestroyModelMixin,
                     GenericAPIView):
    queryset = RoomMarker.objects.all()
    serializer_class = RoomMarkerSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
