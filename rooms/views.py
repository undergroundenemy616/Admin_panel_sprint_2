from typing import Dict, Optional
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin, RetrieveModelMixin, CreateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from backends.pagination import DefaultPagination
from backends.mixins import FilterListMixin
from rooms.models import Room
from rooms.procedures import select_filtered_rooms
from rooms.serializers import RoomSerializer, FilterRoomSerializer


class ListCreateRoomsView(FilterListMixin,
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
        mapped = {"floor_id": query_params.get('floor'),
                  "type": query_params.get('type'),
                  "tables__tags__title__in": query_params.get('tags')}
        items = []
        for field in mapped.keys():
            if not mapped[field]:
                items.append(field)
        for item in items:
            del mapped[item]
        return mapped

    def get(self, request, *args, **kwargs):
        """Provides filtered list interface."""
        mapped = self.get_mapped_query(request)
        records = select_filtered_rooms()
        return Response(data=records, status=200)

        # mapped = self.get_mapped_query(request)
        # is_exists = Floor.objects.filter(pk=mapped['floor_id'])
        # rooms = Room.objects.all().filter(floor_id=1)
        # tables = Table.objects.all().filter(room_id__in=[r.id for r in rooms])
        #
        # mapped = self.get_mapped_query(request)
        # queryset = self.get_queryset()
        # if mapped:
        #     queryset = queryset.filter(**mapped)
        #
        # queryset = self.filter_queryset(queryset)  # django filtering
        # page = self.paginate_queryset(queryset)  # rest page pagination
        #
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)  # rest response by pagination
        # serializer = self.get_serializer(queryset, many=True)
        # return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveUpdateRoomsView(RetrieveModelMixin,
                              UpdateModelMixin,
                              GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    pagination_class = DefaultPagination

    # permission_classes = (IsAdminUser,)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
