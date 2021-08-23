import orjson
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import Response, status

from bookings.models import Booking
from core.permissions import IsAuthenticated
from files.serializers_mobile import MobileBaseFileSerializer
from rooms.models import Room, RoomType
from rooms.serializers import TestRoomSerializer
from rooms.serializers_mobile import (MobileRoomMarkerSerializer,
                                      SuitableRoomParameters,
                                      MobileShortRoomSerializer)
from tables.models import Table
from tables.serializers_mobile import MobileTableMarkerSerializer


class SuitableRoomsMobileView(GenericAPIView):
    queryset = Room.objects.all()
    serializer_class = TestRoomSerializer
    pagination_class = None
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(query_serializer=SuitableRoomParameters)
    def get(self, request, *args, **kwargs):
        serializer = SuitableRoomParameters(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        office = serializer.data.get('office')
        date_from = serializer.data.get('date_from')
        date_to = serializer.data.get('date_to')
        quantity = serializer.data.get('quantity')

        """-------------------LOCALIZATION--------------------"""
        predefined_room_types = RoomType.objects.filter(office_id=office,
                                                        is_deletable=False).values('title')
        language = 'en' if predefined_room_types[0]['title'][1] in 'abcdefghijklmnopqrstuvwxyz' else 'ru'
        if language == 'ru':
            query_room_type = request.query_params.get('type')
        else:
            if request.query_params.get('type') == 'Рабочее место':
                query_room_type = 'Workplace'
            else:
                query_room_type = 'Meeting room'
        """-------------------LOCALIZATION-----END--------------------"""
        room_type_title = query_room_type

        try:
            room_type = RoomType.objects.get(title=room_type_title, office_id=office, bookable=True)
        except ObjectDoesNotExist:
            return Response("Suitable places not found", status=status.HTTP_200_OK)

        rooms = Room.objects.is_allowed(user_id=request.user.id).filter(floor__office_id=office, type=room_type)

        tables = Table.objects.filter(room__id__in=rooms).select_related('table_marker', 'room',
                                                                         'room__floor', 'room__zone')

        response = []

        if quantity and tables.count() < quantity:
            quantity = tables.count()

        for table in tables:
            if not room_type.unified:
                try:
                    if table.table_marker:
                        response.append({
                            'room': {
                                'id': str(table.room.id),
                                'title': table.room.title
                            },
                            'floor': {
                                'id': str(table.room.floor.id),
                                'title': table.room.floor.title
                            },
                            'table': {
                                'id': str(table.id),
                                'title': table.title,
                                'images': MobileBaseFileSerializer(instance=table.images, many=True).data,
                                'marker': MobileTableMarkerSerializer(instance=table.table_marker).data,
                                'is_available': False if Booking.objects.is_overflowed(table, date_from,
                                                                                       date_to) else True
                            }
                        })
                except Table.table_marker.RelatedObjectDoesNotExist:
                    pass
            elif room_type.unified:
                try:
                    if table.room.room_marker:
                        response.append({
                            'room': {
                                'id': str(table.room.id),
                                'title': table.room.title
                            },
                            'floor': {
                                'id': str(table.room.floor.id),
                                'title': table.room.floor.title
                            },
                            'table': {
                                'id': str(table.id),
                                'title': table.title,
                                'images': MobileBaseFileSerializer(instance=table.images, many=True).data,
                                'marker': MobileRoomMarkerSerializer(instance=table.room.room_marker).data,
                                'is_available': False if Booking.objects.is_overflowed(table, date_from,
                                                                                       date_to) else True
                            }
                        })
                except Room.room_marker.RelatedObjectDoesNotExist:
                    pass
            else:
                break

        if response and quantity:
            response = sorted(response, key=lambda k: k['table']['is_available'], reverse=True)
            return Response(orjson.loads(orjson.dumps(response[:quantity])), status=status.HTTP_200_OK)
        elif response and not quantity:
            response = sorted(response, key=lambda k: k['table']['is_available'], reverse=True)
            return Response(orjson.loads(orjson.dumps(response)), status=status.HTTP_200_OK)
        else:
            return Response("Suitable places not found", status=status.HTTP_200_OK)


class MobileRoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = MobileShortRoomSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.method == "GET":
            return self.queryset.select_related('type')
