from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser
from rooms.models import Room
from tables.models import TableTag
from rooms.serializers import RoomSerializer, FilterRoomSerializer, CreateRoomSerializer
from rest_framework.response import Response
from django.core.paginator import Paginator
from rest_framework import status


class ListHandler(ListAPIView):
    # permission_classes = [IsAdminUser]
    serializer_class = RoomSerializer
    queryset = Room.objects.all()

    def post(self, request):
        """
        Add new room

        """
        serializer = CreateRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kwargs = {
            "floor_id": serializer.data.get('floor'),
            "title": serializer.data.get('title'),
            "description": serializer.data.get('description'),
            "type": serializer.data.get('type')
        }
        room = Room.objects.create(**kwargs)
        room.save()
        return Response(self.serializer_class(room).data, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        """
        Get filtered room

        """
        serializer = FilterRoomSerializer(data=request.query_params)
        if serializer.is_valid():
            filter_dict = {
                "floor_id": serializer.data.get('floor'),
                "type": serializer.data.get('type'),
                "tables__tags__title__in": serializer.data.get('tags')
            }
            rooms = Room.objects.filter(**{key: val for key, val in filter_dict.items() if val is not None}).distinct()
        else:
            rooms = self.get_queryset()
        limit = serializer.data.get('limit') or 20
        start = serializer.data.get('start') or 1
        paged_rooms = Paginator(rooms, limit)
        results = [RoomSerializer(room).data for room in paged_rooms.get_page(start)]
        return Response({
            "start": start,
            "limit": limit,
            "count": len(results),
            "next": "",
            "previous": "",
            "results": results
        })


class ObjectHandler(RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAdminUser]
    serializer_class = RoomSerializer
    queryset = Room.objects.all()

    # TODO: PUT /rooms/<pk> += images, zone
