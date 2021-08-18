import os

from django.db.transaction import atomic
from django.shortcuts import get_list_or_404
from exchangelib import Account as Ac, Credentials, Configuration, DELEGATE
from exchangelib.errors import UnauthorizedError, TransportError
from exchangelib.services import GetRooms
from rest_framework import serializers, status

from core.handlers import ResponseException
from files.serializers import TestBaseFileSerializer
from offices.models import Office
from room_types.models import RoomType
from rooms.models import Room, RoomMarker
from tables.models import Table
from tables.serializers_admin import AdminTableSerializer


class SwaggerRoomList(serializers.Serializer):
    tables = serializers.BooleanField(required=False)


class AdminRoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ['id', 'title', 'description', 'seats_amount']

    def to_representation(self, instance):
        response = super(AdminRoomSerializer, self).to_representation(instance)
        response['floor_id'] = instance.floor.id if instance.floor else None
        response['floor_title'] = instance.floor.title if instance.floor else None
        response['is_bookable'] = instance.type.bookable if instance.type else None
        response['occupied'] = instance.occupied if hasattr(instance, 'occupied') else 0
        response['capacity'] = instance.capacity if hasattr(instance, 'occupied') else instance.tables.count()
        response['suitable_tables'] = instance.free if hasattr(instance, 'suitable_tables') else response['capacity']
        response['zone_id'] = instance.zone.id if instance.zone else None
        response['zone_title'] = instance.zone.title if instance.zone else None
        response['images'] = TestBaseFileSerializer(instance=instance.images, many=True).data
        response['type'] = instance.type.title if instance.type else None
        if instance.type:
            response['room_type_color'] = instance.type.color
            response['room_type_icon'] = TestBaseFileSerializer(instance=instance.type.icon).data if instance.type.icon else None
            response['room_type_unified'] = instance.type.unified if instance.type else None
        else:
            response['room_type_color'] = None
            response['room_type_icon'] = None
            response['room_type_unified'] = None
        response['marker'] = AdminRoomMarkerCreateSerializer(instance=instance.room_marker).data if \
            hasattr(instance, 'room_marker') else None
        return response


class AdminRoomCreateUpdateSerializer(serializers.ModelSerializer):
    icon = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Room
        fields = '__all__'

    @atomic()
    def create(self, validated_data):
        instance = super(AdminRoomCreateUpdateSerializer, self).create(validated_data)
        self.context['tables'] = True
        if instance.type and instance.type.unified and instance.type.bookable:
            Table.objects.create(title=validated_data['type'].title, room_id=instance.id, )
        return instance

    @atomic()
    def update(self, instance, validated_data):
        if hasattr(instance, 'room_marker') and validated_data.get('icon'):
            instance.room_marker.icon = validated_data['icon']
            instance.room_marker.save()
        for image in instance.images.all():
            if str(image.id) not in validated_data.get('images'):
                image.delete()
        if instance.type and validated_data.get('type'):
            if instance.type.unified != validated_data.get('type').unified or \
                    instance.type.bookable != validated_data.get('type').bookable:
                self.context['tables'] = True
                for table in instance.tables.all():
                    table.delete()
                if validated_data['type'].unified and validated_data['type'].bookable:
                    Table.objects.create(title=validated_data['type'].title, room_id=instance.id, )
        return super(AdminRoomCreateUpdateSerializer, self).update(instance, validated_data)

    def to_representation(self, instance):
        if self.context.get('tables'):
            return AdminRoomWithTablesSerializer(instance=instance).data
        return AdminRoomSerializer(instance=instance).data


class AdminRoomWithTablesSerializer(AdminRoomSerializer):
    def to_representation(self, instance):
        response = super(AdminRoomWithTablesSerializer, self).to_representation(instance)
        response['tables'] = AdminTableSerializer(instance=instance.tables.all(), many=True).data
        return response


class AdminRoomListDeleteSerializer(serializers.Serializer):
    rooms = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Room.objects.all()))

    def delete(self):
        query = get_list_or_404(Room, id__in=self.data['rooms'])
        for table in query:
            table.delete()


class AdminRoomMarkerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMarker
        fields = '__all__'


class AdminRoomExchangeCreateSerializer(serializers.Serializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)

    def create(self, validated_data):
        credentials = Credentials(os.environ['EXCHANGE_ADMIN_LOGIN'], os.environ['EXCHANGE_ADMIN_PASS'])
        config = Configuration(server=os.environ['EXCHANGE_SERVER'], credentials=credentials)
        account_exchange = Ac(primary_smtp_address=os.environ['EXCHANGE_ADMIN_LOGIN'], config=config,
                              autodiscover=False, access_type=DELEGATE)
        room_lists = account_exchange.protocol.get_roomlists()
        created_rooms = []
        try:
            room_type = RoomType.objects.get(office=validated_data['office'], unified=True, is_deletable=False)
        except RoomType.DoesNotExist:
            raise ResponseException("Suitable room type not found", status_code=status.HTTP_404_NOT_FOUND)
        for room_list in room_lists:
            rooms = GetRooms(protocol=account_exchange.protocol).call(roomlist=room_list)
            for room in rooms:
                if not Room.objects.filter(exchange_email=room.email_address).exists():
                    r = Room(title=room.name,
                             exchange_email=room.email_address,
                             type=room_type)
                    r.save()
                    table = Table(room=r, title=room.name)
                    table.save()
                    created_rooms.append(r)

        return AdminRoomSerializer(instance=created_rooms, many=True).data
