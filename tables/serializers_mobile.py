from rest_framework import serializers

from bookings.models import Booking
from files.serializers_mobile import MobileBaseFileSerializer
from rooms.models import RoomMarker, Room
from tables.models import Table, TableTag, TableMarker


class MobileBookingRoomMarkerSerializer(serializers.ModelSerializer):
    room_marker_x = serializers.DecimalField(source='x', max_digits=4, decimal_places=2)
    room_marker_y = serializers.DecimalField(source='y', max_digits=4, decimal_places=2)

    class Meta:
        model = RoomMarker
        fields = ['id', 'room_marker_x', 'room_marker_y']


class MobileBookingRoomSerializer(serializers.ModelSerializer):
    marker = MobileBookingRoomMarkerSerializer(read_only=True, source='room_marker')
    type = serializers.CharField(read_only=True, source='type.title')
    room_type_color = serializers.CharField(required=False, read_only=True, source='type.color')

    class Meta:
        model = Room
        fields = ['id', 'title', 'type', 'marker', 'room_type_color']

    def to_representation(self, instance):
        response = super(MobileBookingRoomSerializer, self).to_representation(instance)
        if response['type'] == 'Workplace':
            response['type'] = 'Рабочее место'
        elif response['type'] == 'Meeting room':
            response['type'] = 'Переговорная'
        if instance.type.icon:
            response['room_type_thumb'] = instance.type.icon.thumb if instance.type.icon.thumb else instance.type.icon.path

        return response


class MobileBookingTableMarkerSerializer(serializers.ModelSerializer):
    table_marker_x = serializers.DecimalField(source='x', max_digits=4, decimal_places=2)
    table_marker_y = serializers.DecimalField(source='y', max_digits=4, decimal_places=2)

    class Meta:
        model = TableMarker
        fields = ['id', 'table_marker_x', 'table_marker_y']


class MobileTableSerializer(serializers.ModelSerializer):
    marker = MobileBookingTableMarkerSerializer(read_only=True, required=False, source='table_marker')

    class Meta:
        model = Table
        fields = ['id', 'title', 'marker']


class MobileBaseTableTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = TableTag
        fields = '__all__'
        depth = 1


class MobileTableTagSerializer(serializers.ModelSerializer):
    title = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = TableTag
        fields = '__all__'

    def to_representation(self, instance):
        if isinstance(instance, list):
            response = []
            for table_tag in instance:
                response.append(MobileBaseTableTagSerializer(table_tag).data)
            return response
        else:
            response = MobileBaseTableTagSerializer(instance=instance).data
            if instance.icon:
                response['icon'] = MobileBaseFileSerializer(instance=instance.icon).data
            response = [response]
            return response


class MobileShortTableTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableTag
        fields = ['id', 'title']


class MobileTableSlotsSerializer(serializers.ModelSerializer):
    date = serializers.DateField(required=False, format="%Y-%m-%d",
                                 input_formats=['%Y-%m-%d', 'iso-8601'])
    daily = serializers.IntegerField(required=False)
    monthly = serializers.IntegerField(required=False)

    class Meta:
        model = Booking
        fields = ['date', 'daily', 'monthly']


class MobileDetailedTableSerializer(serializers.ModelSerializer):
    images = MobileBaseFileSerializer(required=False, many=True, allow_null=True)
    tags = MobileShortTableTagSerializer(required=False, many=True, allow_null=True)

    class Meta:
        model = Table
        fields = ['id', 'title', 'description',
                  'is_occupied', 'images', 'tags']

    def to_representation(self, instance):
        response = super(MobileDetailedTableSerializer, self).to_representation(instance)
        response['office'] = {
            'id': instance.room.floor.office.id,
            'title': instance.room.floor.office.title
        }
        response['floor'] = {
            'id': instance.room.floor.id,
            'title': instance.room.floor.title
        }
        response['room'] = {
            'id': instance.room.id,
            'title': instance.room.title,
            'type': instance.room.type.title if instance.room.type else None,
            'images': MobileBaseFileSerializer(instance=instance.room.images, many=True).data
        }
        response['is_bookable'] = True  # Because Oleg, don`t be mad :^(
        return response


class MobileTableMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableMarker
        fields = ['id', 'x', 'y']
