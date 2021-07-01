from rest_framework import serializers

from bookings.models import Booking
from floors.models import Floor
from group_bookings.models import GroupBooking
from offices.models import Office
from rooms.models import Room, RoomMarker
from tables.models import Table
from users.models import Account


class MobileGroupBookingAuthorSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', required=False, read_only=True)
    email = serializers.CharField(source='user.email', required=False, read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'phone_number', 'email']


class MobileGroupBookingOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'title']


class MobileGroupBookingFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'title']


class MobileGroupBookingRoomMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMarker
        fields = ['id', 'x', 'y']


class MobileGroupBookingRoomSerializer(serializers.ModelSerializer):
    marker = MobileGroupBookingRoomMarkerSerializer(read_only=True, source='room_marker')
    type = serializers.CharField(read_only=True, source='type.title')

    class Meta:
        model = Room
        fields = ['id', 'title', 'type', 'marker']


class MobileGroupTableMeetingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'title']


class MobileBookingInfoSerializer(serializers.ModelSerializer):
    office = MobileGroupBookingOfficeSerializer(source='table.room.floor.office', read_only=True)
    floor = MobileGroupBookingFloorSerializer(source='table.room.floor', read_only=True)
    room = MobileGroupBookingRoomSerializer(source='table.room', read_only=True)
    table = MobileGroupTableMeetingInfoSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'date_activate_until', 'table',
                  'is_active', 'room', 'floor', 'office']


class MobileGroupBookingSerializer(serializers.ModelSerializer):
    author = MobileGroupBookingAuthorSerializer(read_only=True)

    class Meta:
        model = GroupBooking
        fields = '__all__'

    def to_representation(self, instance):
        response = super(MobileGroupBookingSerializer, self).to_representation(instance)
        booking_info = MobileBookingInfoSerializer(instance=instance.bookings.all()[0]).data
        response.update(booking_info)

        return response
