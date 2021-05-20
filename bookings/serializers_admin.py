from django.db.transaction import atomic
from rest_framework import serializers

from bookings.models import Booking
from core.handlers import ResponseException
from floors.models import Floor
from offices.models import Office
from room_types.models import RoomType
from rooms.models import Room
from tables.models import Table
from tables.serializers import TestTableSerializer
from users.models import Account


class AdminBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

    @atomic()
    def create(self, validated_data, *args, **kwargs):

        if self.Meta.model.objects.is_user_overflowed(validated_data['user'],
                                                      validated_data['table'].room.type.unified,
                                                      validated_data['date_from'],
                                                      validated_data['date_to']):
            raise ResponseException('User already has a booking for this date.')
        if self.Meta.model.objects.is_overflowed(validated_data['table'],
                                                 validated_data['date_from'],
                                                 validated_data['date_to']):
            raise ResponseException('Table already booked for this date.')

        return self.Meta.model.objects.create(
            date_to=validated_data['date_to'],
            date_from=validated_data['date_from'],
            table=validated_data['table'],
            user=validated_data['user'],
            theme=validated_data['theme'] if 'theme' in validated_data else "Без темы"
        )

    def to_representation(self, instance):
        response = super(AdminBookingCreateSerializer, self).to_representation(instance)
        response['floor_title'] = instance.table.room.floor.title
        response['office_title'] = instance.table.room.floor.office.title
        response['room_title'] = instance.table.room.title
        response['table_title'] = instance.table.title
        return response


class AdminDetailUserForBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class AdminUserForBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'phone_number']


class AdminBookingSerializer(serializers.ModelSerializer):
    user = AdminUserForBookSerializer()

    class Meta:
        model = Booking
        fields = '__all__'

    def to_representation(self, instance):
        response = super(AdminBookingSerializer, self).to_representation(instance)
        response['floor_title'] = instance.table.room.floor.title
        response['office_title'] = instance.table.room.floor.office.title
        response['room_title'] = instance.table.room.title
        response['table_title'] = instance.table.title
        return response


class AdminBookingCreateFastSerializer(serializers.Serializer):
    date_from = serializers.DateTimeField()
    date_to = serializers.DateTimeField()
    user = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all())

    @atomic()
    def create(self, validated_data, *args, **kwargs):
        date_from = validated_data['date_from']
        date_to = validated_data['date_to']
        tables = Table.objects.filter(room__type__id=validated_data['type'].id)
        if Booking.objects.is_user_overflowed(validated_data['user'],
                                              validated_data['type'].unified,
                                              validated_data['date_from'],
                                              validated_data['date_to']):
            raise ResponseException('User already has a booking for this date.')
        for table in tables:
            if not Booking.objects.is_overflowed(table, date_from, date_to):
                return Booking.objects.create(
                    date_to=date_to,
                    date_from=date_from,
                    table=table,
                    user=validated_data['user']
                )
        raise serializers.ValidationError('No table found for fast booking')

    def to_representation(self, instance):
        return AdminBookingCreateSerializer(instance=instance).data

