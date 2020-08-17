from rest_framework.generics import get_object_or_404, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from tables.models import Table, TableTag
from rooms.models import Room
from tables.serializers import TableSerializer, CreateTableSerializer
from rooms.serializers import RoomSerializer
from rest_framework.response import Response


class ListHandler(ListAPIView):
    # permission_classes = [IsAdminUser]
    serializer_class = TableSerializer
    queryset = Table.objects.all()

    def post(self, request):
        """Add new table"""
        serializer = CreateTableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        office_id = RoomSerializer(Room.objects.get(id=serializer.data.get('room'))).data['floor']['office']['id']
        table = Table.objects.create(
            title=serializer.data.get('title'),
            room=Room.objects.get(id=serializer.data.get('room'))
        )
        table.tags.set(TableTag.objects.filter(title__in=serializer.data.get('tags'), office_id=office_id))
        table.save()
        return Response(self.serializer_class(table).data, status=status.HTTP_200_OK)


class ObjectHandler(RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAdminUser]
    serializer_class = TableSerializer
    queryset = Table.objects.all()
