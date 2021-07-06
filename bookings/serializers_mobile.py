from datetime import datetime, timedelta, timezone

from django.core.exceptions import ObjectDoesNotExist, ValidationError as ValErr
from django.core.validators import validate_email
from django.db.transaction import atomic
from django.utils.timezone import now
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from bookings.models import Booking, Table, MINUTES_TO_ACTIVATE
from bookings.serializers import (BaseBookingSerializer,
                                  TestBaseBookingSerializer)
from bookings.validators import BookingTimeValidator
from core.handlers import ResponseException
from core.pagination import DefaultPagination
from group_bookings.models import GroupBooking
from group_bookings.serializers_mobile import MobileGroupBookingSerializer, MobileGroupWorkspaceSerializer
from rooms.models import RoomMarker, Room
from tables.models import TableMarker
from tables.serializers_mobile import MobileTableSerializer, MobileBookingRoomSerializer
from users.models import Account, User
from users.tasks import send_email, send_sms


def calculate_date_activate_until(date_from, date_to):
    date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    date_from = date_from.replace(tzinfo=timezone.utc)
    date_to = date_to.replace(tzinfo=timezone.utc)
    if date_now <= date_from:
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
            response['room'] = MobileBookingRoomSerializer(instance=instance.table.room).data
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
    guests = serializers.JSONField(required=False)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'date_to', 'date_from', 'users', 'room', 'guests']

    def validate(self, attrs):
        if not attrs['room'].type.unified:
            raise ResponseException("Selected table is not for meetings", status_code=status.HTTP_400_BAD_REQUEST)
        if Booking.objects.is_overflowed(table=attrs['room'].tables.all()[0],
                                         date_from=attrs['date_from'],
                                         date_to=attrs['date_to']):
            raise ResponseException("This meeting table is occupied", status_code=status.HTTP_400_BAD_REQUEST)
        if attrs.get('guests'):
            for guest in attrs.get('guests'):
                contact_data = attrs.get('guests')[guest]
                try:
                    validate_email(contact_data)
                    message = f"Здравствуйте, {guest}. Вы были приглашены на встречу, " \
                              f"которая пройдёт в {attrs['room'].floor.office.title}, " \
                              f"этаж {attrs['room'].floor.title}, кабинет {attrs['room'].title}. " \
                              f"Дата и время проведения {datetime.strftime(attrs['date_from'], '%Y-%m-%d %H:%M')} - " \
                              f"{datetime.strftime(attrs['date_to'], '%H:%M')}"
                    send_email.delay(email=contact_data, subject="Встреча", message=message)
                except ValErr:
                    try:
                        contact_data = User.normalize_phone(contact_data)
                        message = f"Здравствуйте, {guest}. Вы были приглашены на встречу, " \
                                  f"которая пройдёт в {attrs['room'].floor.office.title}, " \
                                  f"этаж {attrs['room'].floor.title}, кабинет {attrs['room'].title}. " \
                                  f"Дата и время проведения {datetime.strftime(attrs['date_from'], '%Y-%m-%d %H:%M')} - " \
                                  f"{datetime.strftime(attrs['date_to'], '%H:%M')}"
                        send_sms.delay(phone_number=contact_data, message=message)
                    except ValueError:
                        raise ResponseException("Wrong format of email or phone",
                                                status_code=status.HTTP_400_BAD_REQUEST)
        return attrs

    @atomic()
    def group_create_meeting(self, context):
        author = context['request'].user.account

        group_booking = GroupBooking.objects.create(author=author, guests=self.validated_data.get('guests'))

        bookings_to_create = []
        date_activate_until = calculate_date_activate_until(self.validated_data['date_from'],
                                                            self.validated_data['date_to'])
        for user in self.validated_data['users']:
            bookings_to_create.append(Booking(user=user,
                                              table=self.validated_data['room'].tables.all()[0],
                                              date_to=self.validated_data['date_to'],
                                              date_from=self.validated_data['date_from'],
                                              date_activate_until=date_activate_until,
                                              group_booking=group_booking
                                              ))

        self.Meta.model.objects.bulk_create(bookings_to_create)

        return MobileGroupBookingSerializer(instance=group_booking).data


class MobileWorkplaceGroupBookingSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=Account.objects.all())
    tables = serializers.PrimaryKeyRelatedField(many=True, queryset=Table.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'date_to', 'date_from', 'users', 'tables']

    def validate(self, attrs):
        for table in attrs['tables']:
            if table.room.type.unified:
                raise ResponseException("Selected table is not a workplace", status_code=status.HTTP_400_BAD_REQUEST)

        occupied_tables = []
        for table in attrs['tables']:
            if Booking.objects.is_overflowed(table=table, date_from=attrs['date_from'], date_to=attrs['date_to']):
                occupied_tables.append(table.id)
        if occupied_tables:
            raise ValidationError(detail={
                'occupied_tables': list(set(occupied_tables))
            }, code=status.HTTP_400_BAD_REQUEST)

        if len(attrs['users']) != len(attrs['tables']):
            raise ResponseException("Selected not equal number of users and tables",
                                    status_code=status.HTTP_400_BAD_REQUEST)

        return attrs

    @atomic()
    def group_create_workplace(self, context):
        author = context['request'].user.account

        group_booking = GroupBooking.objects.create(author=author)

        bookings_to_create = []
        date_activate_until = calculate_date_activate_until(self.validated_data['date_from'],
                                                            self.validated_data['date_to'])
        for i in range(len(self.validated_data['users'])):
            bookings_to_create.append(Booking(user=self.validated_data['users'][i],
                                              table=self.validated_data['tables'][i],
                                              date_to=self.validated_data['date_to'],
                                              date_from=self.validated_data['date_from'],
                                              date_activate_until=date_activate_until,
                                              group_booking=group_booking
                                              ))

        self.Meta.model.objects.bulk_create(bookings_to_create)

        return MobileGroupWorkspaceSerializer(instance=group_booking).data
