from datetime import datetime, timedelta, timezone

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.transaction import atomic
from django.utils.timezone import now
from rest_framework import serializers, status

from bookings.models import Booking, Table, MINUTES_TO_ACTIVATE
from bookings.serializers import (BaseBookingSerializer,
                                  TestBaseBookingSerializer)
from bookings.validators import BookingTimeValidator
from core.handlers import ResponseException
from core.pagination import DefaultPagination
from group_bookings.models import GroupBooking
from group_bookings.serializers_mobile import MobileGroupBookingSerializer
from rooms.models import RoomMarker
from tables.models import TableMarker
from tables.serializers_mobile import MobileTableSerializer
from users.models import Account


def calculate_date_activate_until(date_from, date_to):
    date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    date_from = datetime.strptime(date_from.split(".")[0], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    date_to = datetime.strptime(date_to.split(".")[0], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    if date_now <= date_from:  #
        if date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):
            return date_from + timedelta(minutes=MINUTES_TO_ACTIVATE)
        else:
            return date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
    elif date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):
        return date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
    else:
        return date_to


class MobileBookingSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200, default="Без темы")
    user = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True)
    pagination_class = DefaultPagination

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme', 'user', 'group_booking_id']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def to_representation(self, instance):
        try:
            if self.context.method == 'GET':
                response = TestBaseBookingSerializer(instance).data
                response['active'] = response.pop('is_active')
                response['table'] = MobileTableSerializer(instance=instance.table).data
                response['room'] = {
                    "id": instance.table.room.id,
                    "title": instance.table.room.title,
                    "type": instance.table.room.type.title
                    }
                response['floor'] = {
                    "id": instance.table.room.floor.id,
                    "title": instance.table.room.floor.title
                }
                response['office'] = {
                    "id": instance.table.room.floor.office.id,
                    "title": instance.table.room.floor.office.title,
                    "description": instance.table.room.floor.office.description
                }

                remove_keys = ('date_activate_until', 'is_over', 'user', 'theme')

                for key in remove_keys:
                    if key in response:
                        del response[key]

                return response
            elif self.context.method == 'POST':
                response = TestBaseBookingSerializer(instance).data
                response['office'] = {
                    "id": instance.table.room.floor.office.id,
                    "title": instance.table.room.floor.office.title
                }
                response['floor'] = {
                    "id": instance.table.room.floor.id,
                    "title": instance.table.room.floor.title}
                if instance.table.room.type.unified:
                    room_marker = RoomMarker.objects.get(room_id=instance.table.room.id)
                    response['room'] = {
                        "id": instance.table.room.id,
                        "title": instance.table.room.title,
                        "type": instance.table.room.type.title,
                        "marker": {
                            "id": str(room_marker.id),
                            "x": room_marker.x,
                            "y": room_marker.y
                        }
                    }
                else:
                    response['room'] = {
                        "id": instance.table.room.id,
                        "title": instance.table.room.title,
                        "type": instance.table.room.type.title,
                    }
                try:
                    table_marker = TableMarker.objects.get(table_id=instance.table.id)
                except ObjectDoesNotExist:
                    table_marker = None
                if table_marker:
                    response['table'] = {
                        "id": instance.table.id,
                        "title": instance.table.title,
                        "marker": {
                            "id": str(table_marker.id),
                            "x": table_marker.x,
                            "y": table_marker.y
                        }
                    }
                else:
                    response['table'] = {
                        "id": instance.table.id,
                        "title": instance.table.title
                    }
                response['active'] = response.pop('is_active')
                remove_keys = ('theme', 'is_over', 'user')
                for key in remove_keys:
                    if key in response:
                        del response[key]
                return response
        except AttributeError:
            response = TestBaseBookingSerializer(instance).data
            response['active'] = response.pop('is_active')
            response['table'] = MobileTableSerializer(instance=instance.table).data
            response['room'] = {
                "id": instance.table.room.id,
                "title": instance.table.room.title,
                "type": instance.table.room.type.title
            }
            response['floor'] = {
                "id": instance.table.room.floor.id,
                "title": instance.table.room.floor.title
            }
            response['office'] = {
                "id": instance.table.room.floor.office.id,
                "title": instance.table.room.floor.office.title,
                "description": instance.table.room.floor.office.description
            }

            remove_keys = ('date_activate_until', 'is_over', 'user', 'theme')

            for key in remove_keys:
                if key in response:
                    del response[key]

            return response

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
        if validated_data['table'].room.type.unified:
            return self.Meta.model.objects.create(
                date_to=validated_data['date_to'],
                date_from=validated_data['date_from'],
                table=validated_data['table'],
                user=validated_data['user'],
                theme=validated_data['theme']
            )
        return self.Meta.model.objects.create(
            date_to=validated_data['date_to'],
            date_from=validated_data['date_from'],
            table=validated_data['table'],
            user=validated_data['user']
        )


class MobileBookingActivateActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)

    class Meta:
        model = Booking
        fields = ["booking"]

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance).data
        return response

    def update(self, instance, validated_data):
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        if not date_now < instance.date_activate_until:
            raise serializers.ValidationError('Activation time have passed')
        instance.set_booking_active()
        return instance


class MobileBookingDeactivateActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Booking
        fields = ['booking']

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance=instance).to_representation(instance=instance)
        return response

    def update(self, instance, validated_data):
        now_date = now()
        if instance.date_activate_until > now_date and not instance.is_active:
            instance.set_booking_over()
            return instance
        flag = {'status': 'over'}
        instance.set_booking_over(kwargs=flag)
        return instance


class MobileBookingSerializerForTableSlots(serializers.ModelSerializer):
    active = serializers.BooleanField(source='is_active')

    class Meta:
        model = Booking
        fields = ['id', 'date_from', 'date_to', 'date_activate_until', 'is_over',
                  'theme', 'status', 'user', 'table', 'active']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def to_representation(self, instance):
        response = super(MobileBookingSerializerForTableSlots, self).to_representation(instance)
        return response


class MobileMeetingGroupBookingSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=Account.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'date_to', 'date_from', 'users', 'table']

    @atomic()
    def group_create(self, validated_data, context):
        author = Account.objects.get(user_id=context['request'].user.id)
        users = Account.objects.filter(id__in=validated_data['users'])
        table = Table.objects.filter(id=validated_data['table'],
                                     room__type__bookable=True,
                                     room__type__unified=True,
                                     room__type__is_deletable=False).select_related('room__type')
        if table:
            table = table.get(id=validated_data['table'])
        else:
            raise ResponseException("Selected table is not for meetings", status_code=status.HTTP_400_BAD_REQUEST)
        booking_of_table = Booking.objects.filter(Q(table=table)
                                                  &
                                                  Q(status__in=['active', 'waiting'])
                                                  &
                                                  (Q(date_from__lt=validated_data['date_to'],
                                                     date_to__gte=validated_data['date_to'])
                                                   |
                                                   Q(date_from__lte=validated_data['date_from'],
                                                     date_to__gt=validated_data['date_from'])
                                                   |
                                                   Q(date_from__gte=validated_data['date_from'],
                                                     date_to__lte=validated_data['date_to']))
                                                  & Q(date_from__lt=validated_data['date_to'])
                                                  )
        if booking_of_table:
            raise ResponseException("This meeting table is occupied", status_code=status.HTTP_400_BAD_REQUEST)
        group_booking = GroupBooking.objects.create(author=author)
        if validated_data.get('guests'):
            group_booking.guests = validated_data.get('guests')
            group_booking.save()

        bookings_to_create = []
        date_activate_until = calculate_date_activate_until(validated_data['date_from'], validated_data['date_to'])
        for user in users:
            bookings_to_create.append(Booking(user=user,
                                              table=table,
                                              date_to=validated_data['date_to'],
                                              date_from=validated_data['date_from'],
                                              date_activate_until=date_activate_until,
                                              group_booking=group_booking
                                              ))

        self.Meta.model.objects.bulk_create(bookings_to_create)

        return MobileGroupBookingSerializer(instance=group_booking).data
