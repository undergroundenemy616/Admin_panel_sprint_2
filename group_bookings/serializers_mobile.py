from rest_framework import serializers

from bookings.models import Booking
from floors.models import Floor
from group_bookings.models import GroupBooking
from offices.models import Office
from rooms.models import Room, RoomMarker
from tables.models import Table, TableMarker
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
    marker = MobileGroupBookingRoomMarkerSerializer(required=False, read_only=True, source='room_marker')
    type = serializers.CharField(read_only=True, source='type.title')

    class Meta:
        model = Room
        fields = ['id', 'title', 'type', 'marker']


class MobileGroupBookingTableMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableMarker
        fields = ['id', 'x', 'y']


class MobileGroupTableMeetingInfoSerializer(serializers.ModelSerializer):
    marker = MobileGroupBookingTableMarkerSerializer(required=False, read_only=True, source='table_marker')

    class Meta:
        model = Table
        fields = ['id', 'title', 'marker']


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
        response['users'] = MobileGroupBookingAuthorSerializer(instance=Account.objects.filter(booking__in=instance.bookings.all()).select_related('user'), many=True).data
        response.update(booking_info)

        return response


class MobileGroupWorkspaceBookingInfoSerializer(MobileBookingInfoSerializer):
    user = MobileGroupBookingAuthorSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'table', 'room', 'floor', 'user']


class MobileGroupWorkspaceSerializer(serializers.ModelSerializer):
    author = MobileGroupBookingAuthorSerializer(read_only=True)

    class Meta:
        model = GroupBooking
        fields = ['id', 'author']

    def to_representation(self, instance):
        response = super(MobileGroupWorkspaceSerializer, self).to_representation(instance)
        response['bookings_info'] = MobileGroupWorkspaceBookingInfoSerializer(instance=instance.bookings.all(),
                                                                              many=True).data
        response['date_from'] = instance.bookings.all()[0].date_from
        response['date_to'] = instance.bookings.all()[0].date_to
        response['office'] = MobileGroupBookingOfficeSerializer(instance=instance.bookings.all()[0].table.room.floor.office).data

        return response
