from rest_framework import serializers

from bookings.models import Booking
from floors.models import Floor
from group_bookings.models import GroupBooking
from offices.models import Office
from rooms.models import Room, RoomMarker
from tables.models import Table
from users.models import Account


class AdminGroupBookingAuthorSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', required=False, read_only=True)
    email = serializers.CharField(source='user.email', required=False, read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'phone_number', 'email']


class AdminGroupBookingOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'title']


class AdminGroupBookingFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'title']


class AdminGroupBookingRoomMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMarker
        fields = ['id', 'x', 'y']


class AdminGroupBookingRoomSerializer(serializers.ModelSerializer):
    marker = AdminGroupBookingRoomMarkerSerializer(read_only=True, source='room_marker')
    type = serializers.CharField(read_only=True, source='type.title')

    class Meta:
        model = Room
        fields = ['id', 'title', 'type', 'marker']


class AdminGroupTableMeetingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'title']


class AdminBookingInfoSerializer(serializers.ModelSerializer):
    office = AdminGroupBookingOfficeSerializer(source='table.room.floor.office', read_only=True)
    floor = AdminGroupBookingFloorSerializer(source='table.room.floor', read_only=True)
    room = AdminGroupBookingRoomSerializer(source='table.room', read_only=True)
    unified = serializers.BooleanField(source='table.room.type.unified', read_only=True)
    table = AdminGroupTableMeetingInfoSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'date_from', 'date_to', 'date_activate_until', 'table',
                  'is_active', 'room', 'floor', 'office', 'user', 'unified']


class AdminGroupBookingSerializer(serializers.ModelSerializer):
    author = AdminGroupBookingAuthorSerializer(read_only=True)

    class Meta:
        model = GroupBooking
        fields = '__all__'

    def to_representation(self, instance):
        response = super(AdminGroupBookingSerializer, self).to_representation(instance)
        booking_info = AdminBookingInfoSerializer(instance=instance.bookings.all(), many=True).data
        response['users'] = AdminGroupBookingAuthorSerializer(instance=Account.objects.filter(
            booking__in=instance.bookings.all()).select_related('user'), many=True).data
        for booking in booking_info:
            for user in response['users']:
                if user['id'] == str(booking['user']):
                    user['booking_id'] = booking.pop('id')
        for booking in booking_info:
            booking.pop('user')
            response['unified'] = booking.pop('unified')
        if instance.bookings.all().count() == instance.bookings.filter(is_over=True).count():
            response['is_over'] = True
        else:
            response['is_over'] = False
        response.update(booking_info[0])

        return response


class AdminGroupWorkspaceBookingInfoSerializer(AdminBookingInfoSerializer):
    user = AdminGroupBookingAuthorSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'table', 'room', 'floor', 'user']


class AdminGroupWorkspaceSerializer(serializers.ModelSerializer):
    author = AdminGroupBookingAuthorSerializer(read_only=True)

    class Meta:
        model = GroupBooking
        fields = ['id', 'author']

    def to_representation(self, instance):
        response = super(AdminGroupWorkspaceSerializer, self).to_representation(instance)
        response['bookings_info'] = AdminGroupWorkspaceBookingInfoSerializer(instance=instance.bookings.all(),
                                                                             many=True).data
        response['date_from'] = instance.bookings.all()[0].date_from
        response['date_to'] = instance.bookings.all()[0].date_to
        response['office'] = AdminGroupBookingOfficeSerializer(
            instance=instance.bookings.all()[0].table.room.floor.office).data
        response['unified'] = instance.bookings.all()[0].table.room.type.unified

        return response


class AdminGroupCombinedSerializer(serializers.ModelSerializer):
    author = AdminGroupBookingAuthorSerializer(read_only=True)

    class Meta:
        model = GroupBooking
        fields = ['id', 'author']

    def to_representation(self, instance):
        response = super(AdminGroupCombinedSerializer, self).to_representation(instance)
        response['bookings_info'] = AdminGroupWorkspaceBookingInfoSerializer(instance=instance.bookings.all(),
                                                                             many=True).data
        response['unified'] = instance.bookings.all()[0].table.room.type.unified

        return response

