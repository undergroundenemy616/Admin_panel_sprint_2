from datetime import datetime, timedelta, timezone

import pytz
from django.core.exceptions import ValidationError as ValErr
from django.core.validators import validate_email
from django.db.transaction import atomic
from django.utils.timezone import now
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from bookings.models import Booking, Table, MINUTES_TO_ACTIVATE
from bookings.serializers import BaseBookingSerializer
from bookings.validators import BookingTimeValidator
from core.handlers import ResponseException
from core.pagination import DefaultPagination
from group_bookings.models import GroupBooking
from group_bookings.serializers_mobile import (MobileGroupBookingSerializer,
                                               MobileGroupWorkspaceSerializer,
                                               MobileGroupBookingFloorSerializer, MobileGroupBookingAuthorSerializer)
from offices.models import Office
from rooms.models import RoomMarker, Room
from tables.models import TableMarker
from tables.serializers_mobile import MobileBookingRoomSerializer
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


class MobileBookingOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'title', 'description']


class MobileCreateBookingTableMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableMarker
        fields = ['id', 'x', 'y']


class MobileBookingTableSerializer(serializers.ModelSerializer):
    marker = MobileCreateBookingTableMarkerSerializer(read_only=True, required=False, source='table_marker')

    class Meta:
        model = Table
        fields = ['id', 'title', 'marker']


class MobileBookingSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    room = MobileBookingRoomSerializer(required=False, source='table.room', read_only=True)
    floor = MobileGroupBookingFloorSerializer(required=False, source='table.room.floor', read_only=True)
    office = MobileBookingOfficeSerializer(required=False, source='table.room.floor.office', read_only=True)
    theme = serializers.CharField(max_length=200, default="Без темы")
    user = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True)
    active = serializers.BooleanField(source='is_active', required=False, read_only=True)
    group_booking_author = MobileGroupBookingAuthorSerializer(source='group_booking.author', required=False, read_only=True)
    pagination_class = DefaultPagination

    class Meta:
        model = Booking
        fields = ['id', 'date_from', 'date_to',
                  'table', 'theme', 'user',
                  'group_booking', 'group_booking_author',
                  'status', 'active',
                  'room', 'floor', 'office']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def to_representation(self, instance):
        try:
            if self.context.method == 'GET':
                if instance.table.room.type.unified and not instance.group_booking:
                    group_booking = GroupBooking.objects.create(author=instance.user, guests=[])
                    instance.group_booking = group_booking
                    instance.save()
                response = super(MobileBookingSerializer, self).to_representation(instance)
                response['table'] = MobileBookingTableSerializer(instance=instance.table).data
                if instance.group_booking and instance.group_booking.author == instance.user:
                    response['is_owner'] = True
                    if instance.group_booking.bookings.all()[0].table.room.type.unified:
                        response['number_of_users'] = instance.group_booking.bookings.count() + \
                                                      len(instance.group_booking.guests)
                    else:
                        response['number_of_users'] = instance.group_booking.bookings.count()
                elif instance.group_booking and instance.group_booking.author != instance.user:
                    response['is_owner'] = False
                    if instance.group_booking.bookings.all()[0].table.room.type.unified:
                        response['number_of_users'] = instance.group_booking.bookings.count() + \
                                                      len(instance.group_booking.guests)
                    else:
                        response['number_of_users'] = instance.group_booking.bookings.count()

                return response
            elif self.context.method == 'POST':
                response = super(MobileBookingSerializer, self).to_representation(instance)
                response['table'] = MobileBookingTableSerializer(instance=instance.table).data
                if instance.table.room.type.unified:
                    room_marker = RoomMarker.objects.get(room_id=instance.table.room_id)
                    response['room'] = {
                        "id": instance.table.room_id,
                        "title": instance.table.room.title,
                        "type": instance.table.room.type.title,
                        "marker": {
                            "id": str(room_marker.id),
                            "x": room_marker.x,
                            "y": room_marker.y
                        }
                    }

                return response
        except AttributeError:
            if instance.table.room.type.unified and not instance.group_booking:
                group_booking = GroupBooking.objects.create(author=instance.user, guests=[])
                instance.group_booking = group_booking
                instance.save()
            response = super(MobileBookingSerializer, self).to_representation(instance)
            response['table'] = MobileBookingTableSerializer(instance=instance.table).data
            if instance.group_booking and instance.group_booking.author == instance.user:
                response['is_owner'] = True
                if instance.group_booking.bookings.all()[0].table.room.type.unified:
                    response['number_of_users'] = instance.group_booking.bookings.count() + \
                                                  len(instance.group_booking.guests)
                else:
                    response['number_of_users'] = instance.group_booking.bookings.count()
            elif instance.group_booking and instance.group_booking.author != instance.user:
                response['is_owner'] = False
                if instance.group_booking.bookings.all()[0].table.room.type.unified:
                    response['number_of_users'] = instance.group_booking.bookings.count() + \
                                                  len(instance.group_booking.guests)
                else:
                    response['number_of_users'] = instance.group_booking.bookings.count()

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
                theme=validated_data['theme'],
                kwargs=self.context.headers.get('Language', None)
            )
        return self.Meta.model.objects.create(
            date_to=validated_data['date_to'],
            date_from=validated_data['date_from'],
            table=validated_data['table'],
            user=validated_data['user'],
            kwargs=self.context.headers.get('Language', None)
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
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=Account.objects.all(), required=True)
    guests = serializers.ListField(child=serializers.JSONField(), allow_empty=True, required=False)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'date_to', 'date_from', 'users', 'room', 'guests']

    def validate(self, attrs):
        office = Office.objects.get(id=attrs['room'].floor.office_id)
        time_zone = pytz.timezone(office.timezone).utcoffset(datetime.now())
        message_date_from = attrs['date_from'] + time_zone
        message_date_to = attrs['date_to'] + time_zone

        if not attrs['room'].type.unified:
            raise ResponseException("Selected table is not for meetings", status_code=status.HTTP_400_BAD_REQUEST)

        if Booking.objects.is_overflowed(table=attrs['room'].tables.all()[0],
                                         date_from=attrs['date_from'],
                                         date_to=attrs['date_to']):
            raise ResponseException("This meeting table is occupied", status_code=status.HTTP_400_BAD_REQUEST)

        if attrs.get('guests'):
            for guest in attrs.get('guests'):
                guest_name = list(guest.keys())[0]
                contact_data = guest[guest_name]
                try:
                    validate_email(contact_data)
                    if self.context['request'].headers.get('Language', None) == 'ru':
                        message = f"Здравствуйте, {guest_name}. Вы были приглашены на встречу, " \
                                  f"которая пройдёт в {attrs['room'].floor.office.title}, " \
                                  f"этаж {attrs['room'].floor.title}, кабинет {attrs['room'].title}. " \
                                  f"Дата и время проведения {datetime.strftime(message_date_from, '%d.%m.%Y %H:%M')}-" \
                                  f"{datetime.strftime(message_date_to, '%H:%M')}"
                        send_email.delay(email=contact_data, subject="Встреча", message=message)
                    else:
                        message = f"Hello, {guest_name}. You invited to meeting, " \
                                  f"that take place at {attrs['room'].floor.office.title}, " \
                                  f"floor {attrs['room'].floor.title}, room {attrs['room'].title}. " \
                                  f"Meeting date and time {datetime.strftime(message_date_from, '%d.%m.%Y %H:%M')}-" \
                                  f"{datetime.strftime(message_date_to, '%H:%M')}"
                        send_email.delay(email=contact_data, subject="Meeting", message=message)
                except ValErr:
                    try:
                        contact_data = User.normalize_phone(contact_data)
                        if self.context['request'].headers.get('Language', None) == 'ru':
                            message = f"Здравствуйте, {guest_name}. Вы были приглашены на встречу, " \
                                      f"которая пройдёт в {attrs['room'].floor.office.title}, " \
                                      f"этаж {attrs['room'].floor.title}, кабинет {attrs['room'].title}. " \
                                      f"Дата и время проведения {datetime.strftime(message_date_from, '%d.%m.%Y %H:%M')}-" \
                                      f"{datetime.strftime(message_date_to, '%H:%M')}"
                        else:
                            message = f"Hello, {guest_name}. You invited to meeting, " \
                                      f"that take place at {attrs['room'].floor.office.title}, " \
                                      f"floor {attrs['room'].floor.title}, room {attrs['room'].title}. " \
                                      f"Meeting date and time {datetime.strftime(message_date_from, '%d.%m.%Y %H:%M')}-" \
                                      f"{datetime.strftime(message_date_to, '%H:%M')}"
                        send_sms.delay(phone_number=contact_data, message=message)
                    except ValueError:
                        raise ResponseException("Wrong format of email or phone",
                                                status_code=status.HTTP_400_BAD_REQUEST)
        return attrs

    @atomic()
    def group_create_meeting(self, context):
        author = context['request'].user.account

        group_booking = GroupBooking.objects.create(author=author, guests=self.validated_data.get('guests'))

        date_activate_until = calculate_date_activate_until(self.validated_data['date_from'],
                                                            self.validated_data['date_to'])
        my_booking_id = None
        language = self.context['request'].headers.get('Language', None)
        for user in self.validated_data['users']:
            b = Booking(user=user,
                        table=self.validated_data['room'].tables.all()[0],
                        date_to=self.validated_data['date_to'],
                        date_from=self.validated_data['date_from'],
                        date_activate_until=date_activate_until,
                        group_booking=group_booking,
                        theme='Без темы' if language == 'ru' else 'No theme')
            b.save(kwargs=self.context['request'].headers.get('Language', None))
            if user == author:
                my_booking_id = str(b.id)
        response = MobileGroupBookingSerializer(instance=group_booking).data
        response['id'] = my_booking_id
        return response


class MobileWorkplaceGroupBookingSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=Account.objects.all(), required=True)
    tables = serializers.PrimaryKeyRelatedField(many=True, queryset=Table.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'date_to', 'date_from', 'users', 'tables']

    def validate(self, attrs):
        office = Office.objects.get(id=attrs['tables'][0].room.floor.office_id)
        open_time, close_time = office.working_hours.split('-')
        open_time = datetime.strptime(open_time, '%H:%M')
        close_time = datetime.strptime(close_time, '%H:%M')
        if not open_time.time() <= attrs['date_from'].time() <= close_time.time() and not \
                open_time.time() <= attrs['date_to'].time() <= close_time.time():
            raise ResponseException('The selected time does not fall into the office work schedule',
                                    status_code=status.HTTP_400_BAD_REQUEST)
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

        date_activate_until = calculate_date_activate_until(self.validated_data['date_from'],
                                                            self.validated_data['date_to'])
        my_booking_id = None

        for i in range(len(self.validated_data['users'])):
            b = Booking(user=self.validated_data['users'][i],
                        table=self.validated_data['tables'][i],
                        date_to=self.validated_data['date_to'],
                        date_from=self.validated_data['date_from'],
                        date_activate_until=date_activate_until,
                        group_booking=group_booking)
            b.save(kwargs=self.context['request'].headers.get('Language', None))
            if self.validated_data['users'][i] == author:
                my_booking_id = str(b.id)
        response = MobileGroupBookingSerializer(instance=group_booking).data
        response['id'] = my_booking_id

        return MobileGroupWorkspaceSerializer(instance=group_booking).data
