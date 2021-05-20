from datetime import datetime, timedelta, timezone

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from rest_framework import serializers

from bookings.models import Booking, Table
from bookings.serializers import (BaseBookingSerializer,
                                  TestBaseBookingSerializer)
from bookings.validators import BookingTimeValidator
from core.handlers import ResponseException
from core.pagination import DefaultPagination
from mail import send_html_email_message_booking_for_sleep
from rooms.models import RoomMarker
from tables.models import TableMarker
from tables.serializers_mobile import MobileTableSerializer
from users.models import Account


class MobileBookingSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200, default="Без темы")
    user = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True)
    pagination_class = DefaultPagination

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme', 'user']

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
        if validated_data['table'].room.title == 'Капсула сна':
            try:
                office_email = validated_data['table'].room.floor.office.service_email
                subject = "Совершено бронирование капсулы сна!"
                send_html_email_message_booking_for_sleep(
                    to=office_email,
                    subject=subject,
                    message=f"Было совершено бронирование капсулы сна пользователем "
                            f"{validated_data['user'].user.phone_number if validated_data['user'].user.phone_number else validated_data['user'].user.email} "
                            f"c {str(validated_data['date_from'] + timedelta(hours=3))[:16]} "
                            f"до {str(validated_data['date_to'] + timedelta(hours=3))[:16]}"
                )
            except Exception as e:
                pass
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
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200, default="Без темы")
    user = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme', 'user']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance).data
        response['active'] = response['is_active']
        del response['is_active']
        response['user'] = instance.user_id
        response['table'] = instance.table_id
        return response
