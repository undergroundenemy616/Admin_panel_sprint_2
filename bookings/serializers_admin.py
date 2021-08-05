import os
import uuid
from calendar import monthrange
from collections import Counter
from datetime import datetime, date, timedelta
from pathlib import Path
from time import strptime
import pandas as pd
import pytz
import requests
import xlsxwriter
import orjson

from django.core.exceptions import ValidationError as ValErr
from django.core.validators import validate_email
from django.db.models import Q, F, Func
from django.db.transaction import atomic
import pdfkit
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from workalendar.europe import Russia

from booking_api_django_new.filestorage_auth import check_token
from booking_api_django_new.settings import FILES_HOST
from bookings.models import Booking
from bookings.serializers_mobile import calculate_date_activate_until
from core.handlers import ResponseException
from core.utils import get_localization
from files.models import File
from group_bookings.models import GroupBooking
from group_bookings.serializers_admin import AdminGroupBookingSerializer, AdminGroupWorkspaceSerializer
from offices.models import Office
from room_types.models import RoomType
from rooms.models import Room
from tables.models import Table, TableMarker
from users.models import Account, User
from users.tasks import send_email, send_sms


class BookingEmployeeStats(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(required=False, source='id', read_only=True)
    table_id = serializers.UUIDField(required=False, read_only=True)
    table_title = serializers.CharField(required=False, source='table.title', read_only=True)
    office_id = serializers.UUIDField(required=False, source='table.room.floor.office_id', read_only=True)
    office_title = serializers.CharField(required=False, source='table.room.floor.office.title', read_only=True)
    floor_title = serializers.CharField(required=False, source='table.room.floor.title', read_only=True)
    user_id = serializers.UUIDField(required=False, read_only=True)
    first_name = serializers.CharField(required=False, source='user.first_name', read_only=True)
    middle_name = serializers.CharField(required=False, source='user.middle_name', read_only=True)
    last_name = serializers.CharField(required=False, source='user.last_name', read_only=True)
    phone_number1 = serializers.CharField(required=False, source='user.phone_number', read_only=True)
    phone_number2 = serializers.CharField(required=False, source='user.user.phone_number', read_only=True)
    book_status = serializers.CharField(required=False, source='status', read_only=True)
    date_from = serializers.DateTimeField(required=False, read_only=True)
    date_to = serializers.DateTimeField(required=False, read_only=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'table_id', 'table_title', 'office_id', 'office_title',
                  'floor_title', 'user_id', 'first_name', 'middle_name', 'last_name',
                  'phone_number1', 'phone_number2', 'date_to', 'date_from', 'book_status']


class BookingFutureStats(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(required=False, source='id', read_only=True)
    table_id = serializers.UUIDField(required=False, read_only=True)
    table_title = serializers.CharField(required=False, source='table.title', read_only=True)
    office_id = serializers.UUIDField(required=False, source='table.room.floor.office_id', read_only=True)
    office_title = serializers.CharField(required=False, source='table.room.floor.office.title', read_only=True)
    floor_title = serializers.CharField(required=False, source='table.room.floor.title', read_only=True)
    user_id = serializers.UUIDField(required=False, read_only=True)
    first_name = serializers.CharField(required=False, source='user.first_name', read_only=True)
    middle_name = serializers.CharField(required=False, source='user.middle_name', read_only=True)
    last_name = serializers.CharField(required=False, source='user.last_name', read_only=True)
    phone_number_1 = serializers.CharField(required=False, source='user.phone_number', read_only=True)
    phone_number_2 = serializers.CharField(required=False, source='user.user.phone_number', read_only=True)
    book_status = serializers.CharField(required=False, source='status', read_only=True)
    date_from = serializers.DateTimeField(required=False, read_only=True)
    date_to = serializers.DateTimeField(required=False, read_only=True)
    date_activate_until = serializers.DateTimeField(required=False, read_only=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'table_id', 'table_title', 'office_id', 'office_title',
                  'floor_title', 'user_id', 'first_name', 'middle_name', 'last_name',
                  'phone_number_1', 'phone_number_2', 'date_to', 'date_from', 'book_status', 'date_activate_until']


def get_duration(duration):
    hours = int(duration / 3600)
    minutes = int(duration % 3600 / 60)
    seconds = int((duration % 3600) % 60)
    return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


def most_frequent(List):
    occurrence_count = Counter(List)
    return occurrence_count.most_common(1)[0][0]


def date_validation(date):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except:
        raise ResponseException("Wrong date format, should be YYYY-MM-DD")
    return True


def months_between(start_date, end_date):
    if start_date > end_date:
        raise ResponseException(f"Start date {start_date} is not before end date {end_date}",
                                status.HTTP_400_BAD_REQUEST)

    year = start_date.year
    month = start_date.month

    while (year, month) <= (end_date.year, end_date.month):
        yield date(year, month, 1)

        if month == 12:
            month = 1
            year += 1
        else:
            month += 1


class BookingRoomTypeStatsSerializer(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(required=False, source='id', read_only=True)
    room_type_title = serializers.CharField(required=False, source='table.room.type.title', read_only=True)
    office_id = serializers.UUIDField(required=False, source='table.room.floor.office.id', read_only=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'room_type_title', 'office_id']


class AdminUserForBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'phone_number']

    def to_representation(self, instance):
        response = super(AdminUserForBookSerializer, self).to_representation(instance)
        if not instance.phone_number:
            response['phone_number'] = instance.user.phone_number
        return response


class AdminBookingSerializer(serializers.ModelSerializer):
    user = AdminUserForBookSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), write_only=True, source='user')
    floor_title = serializers.CharField(source='table.room.floor.title', read_only=True)
    office_title = serializers.CharField(source='table.room.floor.office.title', read_only=True)
    room_title = serializers.CharField(source='table.room.title', read_only=True)
    table_title = serializers.CharField(source='table.title', read_only=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=False)

    class Meta:
        model = Booking
        fields = '__all__'

    @atomic()
    def create(self, validated_data, *args, **kwargs):
        if not validated_data.get('table'):
            raise ResponseException("Table not specified")

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
            theme=validated_data['theme'] if 'theme' in validated_data else "Без темы",
            kwargs=self.context['request'].headers.get('Language', None)
        )

    @atomic()
    def to_representation(self, instance):
        if instance.table.room.type.unified and not instance.group_booking:
            group_booking = GroupBooking.objects.create(author=instance.user, guests=[])
            instance.group_booking = group_booking
            instance.save()
        response = super(AdminBookingSerializer, self).to_representation(instance)

        return response


class AdminBookingCreateFastSerializer(AdminBookingSerializer):
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), write_only=True)

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
                    user=validated_data['user'],
                    kwargs=self.context['request'].headers.get('Language', None)
                )
        raise serializers.ValidationError('No table found for fast booking')


class AdminSwaggerDashboard(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=False, format='%Y-%m-%d')
    date_to = serializers.DateField(required=False, format='%Y-%m-%d')


class AdminSwaggerBookingEmployee(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    month = serializers.CharField(required=False, max_length=10)
    year = serializers.IntegerField(required=False, max_value=2500, min_value=1970)
    doc_format = serializers.CharField(required=False, default='xlsx', max_length=4)


class AdminSwaggerBookingFuture(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date = serializers.DateField(required=False, format='%Y-%m-%d')
    doc_format = serializers.CharField(required=False, default='xlsx', max_length=4)


class AdminSwaggerRoomType(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=True, format='%Y-%m-%d')
    date_to = serializers.DateField(required=True, format='%Y-%m-%d')
    doc_format = serializers.CharField(required=False, default='xlsx', max_length=4)


class AdminStatisticsSerializer(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=False, format='%Y-%m-%d')
    date_to = serializers.DateField(required=False, format='%Y-%m-%d')
    month = serializers.CharField(required=False, max_length=10)
    year = serializers.IntegerField(required=False, max_value=2500, min_value=1970)
    date = serializers.DateField(required=False, format='%Y-%m-%d')
    doc_format = serializers.CharField(required=False, default='xlsx', max_length=4)

    def get_statistic(self):
        bookings = Booking.objects.all()
        valid_office_id = None
        if self.data.get('office_id'):
            try:
                valid_office_id = uuid.UUID(self.data.get('office_id')).hex
            except ValueError:
                raise ResponseException("Office ID is not valid", status.HTTP_400_BAD_REQUEST)
        if self.data.get('date_from') and self.data.get('date_to'):
            date_validation(self.data.get('date_from'))
            date_validation(self.data.get('date_to'))
            date_from = self.data.get('date_from')
            date_to = self.data.get('date_to')
        else:
            date_from, date_to = date.today(), date.today()

        if valid_office_id:
            all_tables = Table.objects.filter(Q(room__floor__office_id=valid_office_id) &
                                              Q(room__type__is_deletable=False) &
                                              Q(room__type__bookable=True) &
                                              Q(room__type__unified=False))
            tables_with_markers = TableMarker.objects.filter(Q(table__room__floor__office_id=valid_office_id) &
                                                             Q(table__room__type__is_deletable=False) &
                                                             Q(table__room__type__bookable=True)).count()
            number_of_bookings = bookings.filter(Q(table__room__floor__office_id=valid_office_id) &
                                                 (
                                                         (Q(date_from__date__gte=date_from) &
                                                          Q(date_from__date__lt=date_to))
                                                         |
                                                         (Q(date_from__date__lte=date_from) &
                                                          Q(date_to__date__gte=date_to))
                                                         |
                                                         (Q(date_to__date__gt=date_from) &
                                                          Q(date_to__date__lte=date_to))
                                                 )).count()
            number_of_activated_bookings = bookings.filter(Q(status__in=['active', 'over', 'auto_over']) &
                                                           Q(table__room__floor__office_id=valid_office_id) &
                                                           (
                                                                   (Q(date_from__date__gte=date_from) &
                                                                    Q(date_from__date__lt=date_to))
                                                                   |
                                                                   (Q(date_from__date__lte=date_from) &
                                                                    Q(date_to__date__gte=date_to))
                                                                   |
                                                                   (Q(date_to__date__gt=date_from) &
                                                                    Q(date_to__date__lte=date_to))
                                                           )).count()
            number_of_planned_bookings = bookings.filter(Q(status='waiting') &
                                                         Q(table__room__floor__office_id=valid_office_id) &
                                                         (
                                                                 (Q(date_from__date__gte=date_from) &
                                                                  Q(date_from__date__lt=date_to))
                                                                 |
                                                                 (Q(date_from__date__lte=date_from) &
                                                                  Q(date_to__date__gte=date_to))
                                                                 |
                                                                 (Q(date_to__date__gt=date_from) &
                                                                  Q(date_to__date__lte=date_to))
                                                         )).count()
            bookings_with_hours = bookings.filter(Q(table__room__floor__office_id=valid_office_id) &
                                                  (
                                                          (Q(date_from__date__gte=date_from) &
                                                           Q(date_from__date__lt=date_to))
                                                          |
                                                          (Q(date_from__date__lte=date_from) &
                                                           Q(date_to__date__gte=date_to))
                                                          |
                                                          (Q(date_to__date__gt=date_from) &
                                                           Q(date_to__date__lte=date_to))
            )).annotate(hours=Func(F('date_to'), F('date_from'), function='age'))
            tables_from_booking = bookings.filter(Q(table__room__floor__office_id=valid_office_id)
                                                  &
                                                  Q(table__room__type__is_deletable=False)
                                                  &
                                                  Q(table__room__type__bookable=True)
                                                  &
                                                  Q(table__room__type__unified=False)).only('table_id')
        else:
            all_tables = Table.objects.filter(Q(room__type__is_deletable=False) &
                                              Q(room__type__bookable=True) &
                                              Q(room__type__unified=False))
            tables_with_markers = TableMarker.objects.filter(Q(table__room__type__is_deletable=False) &
                                                             Q(table__room__type__bookable=True)).count()
            number_of_bookings = bookings.filter((Q(date_from__date__gte=date_from) &
                                                  Q(date_from__date__lt=date_to))
                                                 |
                                                 (Q(date_from__date__lte=date_from) &
                                                  Q(date_to__date__gte=date_to))
                                                 |
                                                 (Q(date_to__date__gt=date_from) &
                                                  Q(date_to__date__lte=date_to))).count()

            number_of_activated_bookings = bookings.filter(Q(status__in=['active', 'over', 'auto_over']) &
                                                           (Q(date_from__date__gte=date_from) &
                                                            Q(date_from__date__lt=date_to))
                                                           |
                                                           (Q(date_from__date__lte=date_from) &
                                                            Q(date_to__date__gte=date_to))
                                                           |
                                                           (Q(date_to__date__gt=date_from) &
                                                            Q(date_to__date__lte=date_to))
                                                           ).count()
            number_of_planned_bookings = bookings.filter(Q(status='waiting') &
                                                         (
                                                                 (Q(date_from__date__gte=date_from) &
                                                                  Q(date_from__date__lt=date_to))
                                                                 |
                                                                 (Q(date_from__date__lte=date_from) &
                                                                  Q(date_to__date__gte=date_to))
                                                                 |
                                                                 (Q(date_to__date__gt=date_from) &
                                                                  Q(date_to__date__lte=date_to))
                                                         )).count()
            bookings_with_hours = Booking.objects.filter(
                (Q(date_from__date__gte=date_from) &
                 Q(date_from__date__lt=date_to))
                |
                (Q(date_from__date__lte=date_from) &
                 Q(date_to__date__gte=date_to))
                |
                (Q(date_to__date__gt=date_from) &
                 Q(date_to__date__lte=date_to))).annotate(hours=Func(F('date_to'), F('date_from'), function='age'))
            tables_from_booking = bookings.filter(Q(table__room__type__is_deletable=False)
                                                  &
                                                  Q(table__room__type__bookable=True)
                                                  &
                                                  Q(table__room__type__unified=False)).only('table_id')
        all_accounts = Account.objects.all()

        working_days = 0

        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
        except TypeError:
            pass

        for month in months_between(date_from, date_to):

            num_days = monthrange(year=int(month.strftime("%m %Y").split(" ")[1]),
                                  month=int(month.strftime("%m %Y").split(" ")[0]))[1]

            working_days += num_days

            cal = Russia()

            for i in range(num_days):
                if not cal.is_working_day(date(year=int(month.strftime("%m %Y").split(" ")[1]),
                                               month=int(month.strftime("%m %Y").split(" ")[0]), day=i + 1)):
                    working_days = working_days - 1

        tables_available_for_booking = all_tables.filter(is_occupied=False,
                                                         room__type__unified=False,
                                                         room__type__is_deletable=False,
                                                         room__type__bookable=True).count()
        active_users = all_accounts.count()
        total_tables = Table.objects.filter(room__floor__office_id=valid_office_id,
                                            room__type__unified=False,
                                            room__type__is_deletable=False,
                                            room__type__bookable=True
                                            ).count()

        list_of_booked_tables = []
        for table in tables_from_booking:
            list_of_booked_tables.append(table.table_id)

        list_of_booked_tables = list(set(list_of_booked_tables))

        try:
            percentage_of_tables_available_for_booking = tables_available_for_booking / total_tables * 100
        except ZeroDivisionError:
            percentage_of_tables_available_for_booking = 0

        try:
            share_of_confirmed_bookings = number_of_activated_bookings / number_of_bookings * 100
        except ZeroDivisionError:
            share_of_confirmed_bookings = 0

        sum_of_booking_hours = 0

        for booking in bookings_with_hours:
            booking_hours = (float(booking.hours.days*24) + float(booking.hours.seconds/3600))
            sum_of_booking_hours += booking_hours

        table_hours = working_days * 8 * total_tables

        try:
            recycling_percentage_for_all_workplaces = sum_of_booking_hours / table_hours * 100
        except ZeroDivisionError:
            recycling_percentage_for_all_workplaces = 0

        try:
            percentage_of_registered_tables = tables_with_markers / total_tables * 100
        except ZeroDivisionError:
            percentage_of_registered_tables = 0

        try:
            percent_of_tables_booked_at_least_once = len(list_of_booked_tables) / total_tables * 100
        except ZeroDivisionError:
            percent_of_tables_booked_at_least_once = 0

        try:
            average_booking_time = sum_of_booking_hours / number_of_bookings
        except ZeroDivisionError:
            average_booking_time = 0

        try:
            average_number_of_planned_bookings = number_of_planned_bookings / (date_to-date_from).days
        except ZeroDivisionError:
            average_number_of_planned_bookings = 0

        try:
            average_number_of_confirmed_bookings = number_of_activated_bookings / (date_to-date_from).days
        except ZeroDivisionError:
            average_number_of_confirmed_bookings = 0

        response = {
            "tables_available_for_booking": tables_available_for_booking,
            "percentage_of_tables_available_for_booking": percentage_of_tables_available_for_booking.__round__(2),
            "active_users": active_users,
            "number_of_bookings": number_of_bookings,
            "percent_of_tables_booked_at_least_once": percent_of_tables_booked_at_least_once.__round__(2),
            "share_of_confirmed_bookings": share_of_confirmed_bookings.__round__(2),
            "recycling_percentage_for_all_workplaces": recycling_percentage_for_all_workplaces.__round__(2),
            "percentage_of_registered_tables": percentage_of_registered_tables.__round__(2),
            "average_number_of_planned_bookings": average_number_of_planned_bookings.__round__(2),
            "average_number_of_confirmed_bookings": average_number_of_confirmed_bookings.__round__(2),
            "average_booking_time": average_booking_time.__round__(2),
        }

        return response


class AdminBookingEmployeeStatisticsSerializer(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=False, format='%Y-%m-%d')
    date_to = serializers.DateField(required=False, format='%Y-%m-%d')
    month = serializers.CharField(required=False, max_length=10)
    year = serializers.IntegerField(required=False, max_value=2500, min_value=1970)
    date = serializers.DateField(required=False, format='%Y-%m-%d')

    def get_statistic(self):

        if len(self.data.get('month')) > 10 or \
                int(self.data.get('year')) not in range(1970, 2500):
            return ResponseException("Wrong data")
        if self.data.get('month'):
            month = self.data.get('month')
            month_num = int(strptime(month, '%B').tm_mon)
        else:
            month_num = int(datetime.now().month)
            month = datetime.now().strftime("%B")

        if self.data.get('year'):
            year = int(self.data.get('year'))
        else:
            year = int(datetime.now().year)

        file_name = month + '_' + str(year) + '.xlsx'
        secure_file_name = uuid.uuid4().hex + file_name

        stats = Booking.objects.filter(Q(date_from__month=month_num) &
                                       Q(date_from__year=year) &
                                       Q(status__in=['auto_over', 'auto_canceled',
                                                     'over', 'canceled'])).select_related('table', 'table__room',
                                                                                          'table__room__floor',
                                                                                          'table__room__floor__office',
                                                                                          'user', 'user__user').distinct()

        if self.data.get('office_id'):
            stats = stats.filter(table__room__floor__office_id=self.data.get('office_id'))

        sql_results = BookingEmployeeStats(instance=stats, many=True).data

        if not sql_results:
            raise ResponseException(detail="Data not found", status_code=status.HTTP_404_NOT_FOUND)
        employees = []
        for stat in sql_results:
            employees.append({
                'id': stat['user_id'],
                'first_name': stat['first_name'],
                'middle_name': stat['middle_name'],
                'last_name': stat['last_name'],
                'phone_number': stat.get('phone_number1') if stat.get('phone_number1') else stat.get(
                    'phone_number2'),
                'office_title': stat['office_title'],
                'office_id': stat['office_id'],
                'book_count': 0,
                'over_book': 0,
                'canceled_book': 0,
                'auto_canceled_book': 0,
                'time': 0,
                'places': []
            })

        num_days = monthrange(year=year, month=month_num)[1]

        working_days = num_days

        cal = Russia()

        for i in range(num_days):
            if not cal.is_working_day(date(year=year, month=month_num, day=i + 1)):
                working_days = working_days - 1

        for employee in employees:
            for result in sql_results:
                if result['user_id'] == employee['id'] and result['office_id'] == employee['office_id']:
                    employee['book_count'] = employee['book_count'] + 1
                    if result['book_status'] == 'over' or result['book_status'] == 'auto_over':
                        employee['over_book'] = employee['over_book'] + 1
                    elif result['book_status'] == 'canceled':
                        employee['canceled_book'] = employee['canceled_book'] + 1
                    elif result['book_status'] == 'auto_canceled':
                        employee['auto_canceled_book'] = employee['auto_canceled_book'] + 1
                    employee['time'] = employee['time'] + int(
                        datetime.strptime(result['date_to'].replace("T", " ").
                                          replace("Z", "").split(".")[0],
                                          '%Y-%m-%d %H:%M:%S').timestamp()
                        - datetime.strptime(result['date_from'].replace("T", " ").
                                            replace("Z", "").split(".")[0],
                                            '%Y-%m-%d %H:%M:%S').timestamp())
                    employee['places'].append(str(result['table_id']))
            employee['middle_time'] = str(get_duration(
                timedelta(days=0, seconds=employee['time'] / working_days).total_seconds()
            ))
            employee['middle_booking_time'] = str(get_duration(
                timedelta(days=0, seconds=employee['time'] / employee['book_count']).total_seconds()))
            employee['time'] = str(get_duration(timedelta(days=0, seconds=employee['time']).total_seconds()))

        set_rows = set()

        for employee in employees:
            set_rows.add(orjson.dumps(employee, option=orjson.OPT_SORT_KEYS))

        list_rows = []

        for set_row in set_rows:
            list_rows.append(orjson.loads(set_row))

        for row in list_rows:
            row['places'] = most_frequent(row['places'])

        for table in sql_results:
            for row in list_rows:
                if table['table_id'] == row['places']:
                    row['table'] = "Место: " + table['table_title'] + ", этаж: " + table['floor_title']

        workbook = xlsxwriter.Workbook(secure_file_name)

        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': 1})

        j = 0

        localization = get_localization(self.context, 'statistics')

        for i in range(len(list_rows) + 1):
            i += 1
            if i == 1:
                worksheet.write('A1', localization['full_name'])
                worksheet.write('B1', localization['phone_number'])
                worksheet.write('C1', localization['average_booking_time'])
                worksheet.write('D1', localization['total_booking_time'])
                worksheet.write('E1', localization['average_booking_duration'])
                worksheet.write('F1', localization['number_of_bookings'])
                worksheet.write('G1', localization['number_of_completed_bookings'])
                worksheet.write('H1', localization['number_of_canceled_bookings'])
                worksheet.write('I1', localization['number_of_auto_canceled_bookings'])
                worksheet.write('J1', localization['office'])
                worksheet.write('K1', localization['frequently_booked_seat'])
            else:
                full_name = str(str(list_rows[j].get('last_name')) + ' ' +
                                str(list_rows[j].get('first_name')) + ' ' +
                                str(list_rows[j].get('middle_name'))).replace('None', "")
                if not full_name.replace(" ", ""):
                    full_name = localization['full_name_not_specified']
                worksheet.write('A' + str(i), full_name)
                worksheet.write('B' + str(i), list_rows[j]['phone_number'] if list_rows[j][
                                                                                  'phone_number'] != 'None' else localization['contact_not_specified'])
                worksheet.write('C' + str(i), list_rows[j]['middle_time'])
                worksheet.write('D' + str(i), list_rows[j]['time'])
                worksheet.write('E' + str(i), list_rows[j]['middle_booking_time'])
                worksheet.write('F' + str(i), list_rows[j]['book_count'])
                worksheet.write('G' + str(i), list_rows[j]['over_book'])
                worksheet.write('H' + str(i), list_rows[j]['canceled_book'])
                worksheet.write('I' + str(i), list_rows[j]['auto_canceled_book'])
                worksheet.write('J' + str(i), list_rows[j]['office_title'])
                worksheet.write('K' + str(i), list_rows[j]['table'])
                j += 1

        worksheet.write('A' + str(len(list_rows) + 2), localization['number_of_working_days'], bold)
        worksheet.write('B' + str(len(list_rows) + 2), working_days, bold)

        workbook.close()

        check_token()
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}

        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={"file": (secure_file_name, open(Path(str(Path.cwd()) + "/" + secure_file_name), "rb"),
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers=headers,
            )
        except requests.exceptions.RequestException:
            return {"message": "Error occurred during file upload"}, 500

        response_dict = orjson.loads(response.text)
        file_attrs = {
            "path": FILES_HOST + str(response_dict.get("path")),
            "title": secure_file_name,
            "size": Path(str(Path.cwd()) + "/" + secure_file_name).stat().st_size,
        }
        if response_dict.get("thumb"):
            file_attrs['thumb'] = FILES_HOST + str(response_dict.get("thumb"))

        file_storage_object = File(**file_attrs)
        file_storage_object.save()

        Path(str(Path.cwd()) + "/" + secure_file_name).unlink()

        return file_storage_object


class AdminBookingFutureStatisticsSerializer(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date = serializers.DateField(required=False, format='%Y-%m-%d')
    doc_format = serializers.CharField(required=False, default='xlsx', max_length=4)

    def get_statistic(self):
        date_validation(self.data.get('date'))
        date = self.data.get('date')

        file_name = "future_" + date + '.xlsx'

        stats = Booking.objects.filter(Q(date_from__date=date) &
                                       Q(status__in=['waiting', 'active', 'over', 'auto_over'])).select_related\
            ('table', 'table__room', 'table__room__floor',
             'table__room__floor__office', 'user', 'user__user').distinct()

        if self.data.get('office_id'):
            stats = stats.filter(table__room__floor__office_id=self.data.get('office_id'))

        sql_results = BookingFutureStats(instance=stats, many=True).data

        if not sql_results:
            raise ResponseException(detail="Data not found", status_code=status.HTTP_404_NOT_FOUND)

        secure_file_name = uuid.uuid4().hex + file_name

        workbook = xlsxwriter.Workbook(secure_file_name)

        worksheet = workbook.add_worksheet()

        j = 0

        localization = get_localization(self.context, 'statistics')

        for i in range(len(sql_results) + 1):
            i += 1
            if i == 1:
                worksheet.write('A1', localization['full_name'])
                worksheet.write('B1', localization['phone_number'])
                worksheet.write('C1', localization['beginning_of_booking'])
                worksheet.write('D1', localization['end_of_booking'])
                worksheet.write('E1', localization['duration_of_booking'])
                worksheet.write('F1', localization['office'])
                worksheet.write('G1', localization['floor'])
                worksheet.write('H1', localization['workplace'])
            else:
                full_name = str(str(sql_results[j].get('last_name')) + ' ' +
                                str(sql_results[j].get('first_name')) + ' ' +
                                str(sql_results[j].get('middle_name'))).replace('None', "")
                if not full_name.replace(" ", ""):
                    full_name = localization['full_name_not_specified']
                book_time = float(((datetime.strptime(sql_results[j]['date_to'].replace("T", " ").
                                                      replace("Z", "").split(".")[0],
                                                      '%Y-%m-%d %H:%M:%S')).timestamp() -
                                   datetime.strptime(sql_results[j]['date_from'].replace("T", " ").
                                                     replace("Z", "").split(".")[0],
                                                     '%Y-%m-%d %H:%M:%S').timestamp()) / 3600).__round__(2)

                try:
                    r_date_from = datetime.strptime(sql_results[j]['date_from'].replace("T", " ").split("+")[0],
                                                    '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
                    r_date_to = datetime.strptime(sql_results[j]['date_to'].replace("T", " ").split("+")[0],
                                                  '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
                except ValueError:
                    correct_date_from = sql_results[j]['date_from'].replace("T", " ").split(".")[0]
                    correct_date_to = sql_results[j]['date_from'].replace("T", " ").split(".")[0]
                    r_date_from = datetime.strptime(correct_date_from.replace("T", " ").replace("Z", "").split("+")[0],
                                                    '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
                    r_date_to = datetime.strptime(correct_date_to.replace("T", " ").replace("Z", "").split("+")[0],
                                                  '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)

                phone_number = None
                if sql_results[j]['phone_number_1'] != 'None':
                    phone_number = sql_results[j]['phone_number_1']
                elif sql_results[j]['phone_number_2'] != 'None':
                    phone_number = sql_results[j]['phone_number_2']

                worksheet.write('A' + str(i), full_name)
                worksheet.write('B' + str(i), phone_number if phone_number else localization['contact_not_specified'])
                worksheet.write('C' + str(i), str(r_date_from))
                worksheet.write('D' + str(i), str(r_date_to))
                worksheet.write('E' + str(i), book_time),
                worksheet.write('F' + str(i), str(sql_results[j]['office_title'])),
                worksheet.write('G' + str(i), sql_results[j]['floor_title']),
                worksheet.write('H' + str(i), str(sql_results[j]['table_title']))
                j += 1

        workbook.close()

        check_token()
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}

        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={"file": (secure_file_name, open(Path(str(Path.cwd()) + "/" + secure_file_name), "rb"),
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers=headers,
            )
        except requests.exceptions.RequestException:
            return {"message": "Error occurred during file upload"}, 500

        response_dict = orjson.loads(response.text)
        file_attrs = {
            "path": FILES_HOST + str(response_dict.get("path")),
            "title": secure_file_name,
            "size": Path(str(Path.cwd()) + "/" + secure_file_name).stat().st_size,
        }
        if response_dict.get("thumb"):
            file_attrs['thumb'] = FILES_HOST + str(response_dict.get("thumb"))

        file_storage_object = File(**file_attrs)
        file_storage_object.save()

        Path(str(Path.cwd()) + "/" + secure_file_name).unlink()

        return file_storage_object


class AdminBookingRoomTypeSerializer(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=False, format='%Y-%m-%d')
    date_to = serializers.DateField(required=False, format='%Y-%m-%d')
    month = serializers.CharField(required=False, max_length=10)
    year = serializers.IntegerField(required=False, max_value=2500, min_value=1970)
    date = serializers.DateField(required=False, format='%Y-%m-%d')
    doc_format = serializers.CharField(required=False)

    def get_statistic(self):
        date_validation(self.data.get('date_from'))
        date_validation(self.data.get('date_to'))
        date_from = self.data.get('date_from')
        date_to = self.data.get('date_to')
        doc_format = self.data.get('doc_format')

        file_name = "From_" + date_from + "_To_" + date_to + ".xlsx"
        secure_file_name = uuid.uuid4().hex + file_name

        stats = Booking.objects.filter((
            (Q(date_from__date__gte=date_from) &
             Q(date_from__date__lt=date_to))
            |
            (Q(date_from__date__lte=date_from) &
             Q(date_to__date__gte=date_to))
            |
            (Q(date_to__date__gt=date_from) &
             Q(date_to__date__lte=date_to))
        ) & Q(status__in=['over',
                          'auto_over',
                          'active',
                          'waiting'])).select_related('table', 'table__room',
                                                      'table__room__type',
                                                      'table__room__floor__office').distinct()

        if self.data.get('office_id'):
            stats = stats.filter(table__room__floor__office_id=self.data.get('office_id'))

        set_of_types = set()
        list_of_types = []
        sql_results = BookingRoomTypeStatsSerializer(instance=stats, many=True).data
        for s in sql_results:
            set_of_types.add(s['room_type_title'])
            list_of_types.append(s['room_type_title'])
        number_of_types = len(set_of_types)
        counts = {}
        for i in list_of_types:
            counts[i] = counts.get(i, 0) + 1
        if not sql_results:
            raise ResponseException(detail="Data not found", status_code=status.HTTP_404_NOT_FOUND)
        workbook = xlsxwriter.Workbook(secure_file_name)

        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': 1})

        j = 0

        localization = get_localization(self.context, 'statistics')

        for i in range(len(set_of_types) + 1):
            i += 1
            if i == 1:
                worksheet.write('A1', localization['room_type'])
                worksheet.write('B1', localization['number_of_bookings_for_this_type_of_room'])
            else:
                worksheet.write('A' + str(i), list(set_of_types)[j])
                worksheet.write('B' + str(i), counts.get(list(set_of_types)[j]))
                j += 1

        worksheet.write('A' + str(number_of_types + 2), localization['total_number_of_bookings'], bold)
        worksheet.write('B' + str(number_of_types + 2), len(sql_results), bold)

        chart = workbook.add_chart({'type': 'pie'})

        chart.add_series({
            'name': localization['distribution_of_seat_bookings_by_type'],
            'categories': '=Sheet1!$A$2:$A$' + str(number_of_types + 1),
            'values': '=Sheet1!$B$2:$B$' + str(number_of_types + 1),
            'data_labels': {'percentage': True},
        })

        worksheet.insert_chart('G2', chart, {'x_offset': 25, 'y_offset': 10})

        workbook.close()

        check_token()
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}


        if doc_format:
            if doc_format == 'pdf':
                df = pd.read_excel(Path(str(Path.cwd()) + "/" + secure_file_name))
                df.to_html(Path(str(Path.cwd()) + "/" + secure_file_name.replace('.xlsx', '.html')))
                pdfkit.from_file(secure_file_name.replace('.xlsx', '.html'),
                                 secure_file_name.replace('.xlsx', '.pdf'),
                                 options={'encoding': "utf8"})
                try:
                    response = requests.post(
                        url=FILES_HOST + "/upload",
                        files={
                            "file": (secure_file_name.replace('.xlsx', '.pdf'), open(Path(str(Path.cwd()) + "/" +
                                                                                          secure_file_name.replace(
                                                                                              '.xlsx', '.pdf')),
                                                                                     "rb"),
                                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        headers=headers,
                    )
                except requests.exceptions.RequestException:
                    return {"message": "Error occurred during file upload"}, 500
            elif doc_format == 'xlsx':
                try:
                    response = requests.post(
                        url=FILES_HOST + "/upload",
                        files={
                            "file": (secure_file_name, open(Path(str(Path.cwd()) + "/" + secure_file_name), "rb"),
                                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        headers=headers,
                    )
                except requests.exceptions.RequestException:
                    return {"message": "Error occurred during file upload"}, 500
        if not doc_format:
            try:
                response = requests.post(
                    url=FILES_HOST + "/upload",
                    files={
                        "file": (secure_file_name, open(Path(str(Path.cwd()) + "/" + secure_file_name), "rb"),
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    headers=headers,
                )
            except requests.exceptions.RequestException:
                return {"message": "Error occurred during file upload"}, 500

        response_dict = orjson.loads(response.text)
        file_attrs = {
            "path": FILES_HOST + str(response_dict.get("path")),
            "title": secure_file_name,  # if doc_format == 'xlsx' else secure_file_name.replace('.xlsx', '.pdf'),
            "size": Path(str(Path.cwd()) + "/" + secure_file_name).stat().st_size,  #if
            # doc_format == 'xlsx' else
            # Path(str(Path.cwd()) + "/" + secure_file_name.replace('.xlsx', '.pdf')).stat().st_size,
        }

        if response_dict.get("thumb"):
            file_attrs['thumb'] = FILES_HOST + str(response_dict.get("thumb"))

        file_storage_object = File(**file_attrs)
        file_storage_object.save()

        Path(str(Path.cwd()) + "/" + secure_file_name).unlink()
        try:
            Path(str(Path.cwd()) + "/" + secure_file_name.replace('.xlsx', '.html')).unlink()
            Path(str(Path.cwd()) + "/" + secure_file_name.replace('.xlsx', '.pdf')).unlink()
        except FileNotFoundError:
            pass

        return file_storage_object


class AdminBookingDynamicsOfVisitsSerializer(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=False, format='%Y-%m-%d')
    date_to = serializers.DateField(required=False, format='%Y-%m-%d')

    def get_statistic(self):
        date_validation(self.data.get('date_from'))
        date_validation(self.data.get('date_to'))
        date_from = self.data.get('date_from')
        date_to = self.data.get('date_to')
        valid_office_id = None
        if self.data.get('office_id'):
            try:
                valid_office_id = uuid.UUID(self.data.get('office_id')).hex
            except ValueError:
                raise ResponseException("Office ID is not valid", status.HTTP_400_BAD_REQUEST)

        filtered_bookings = Booking.objects.filter((Q(date_from__date__gte=date_from) &
                                                    Q(date_from__date__lt=date_to))
                                                   |
                                                   (Q(date_from__date__lte=date_from) &
                                                    Q(date_to__date__gte=date_to))
                                                   |
                                                   (Q(date_to__date__gt=date_from) &
                                                    Q(date_to__date__lte=date_to)) &
                                                   Q(status__in=['active', 'waiting', 'over', 'auto_over']))
        if valid_office_id:
            filtered_bookings = filtered_bookings.filter(table__room__floor__office_id=valid_office_id)
        bookings_per_day = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

        for booking in filtered_bookings:
            bookings_per_day[booking.date_from.weekday()] += 1

        file_name = "Dynamics_Of_Visits_From_" + self.data['date_from'] + "_To_" + self.data['date_to'] + ".xlsx"
        secure_file_name = uuid.uuid4().hex + file_name

        localization = get_localization(self.context, 'statistics')

        workbook = xlsxwriter.Workbook(secure_file_name)

        worksheet = workbook.add_worksheet()
        chart = workbook.add_chart({'type': 'column'})
        bold = workbook.add_format({'bold': 1})

        worksheet.write('A1', localization['day_of_week'], bold)
        worksheet.write('B1', localization['number_of_visits'], bold)
        worksheet.write('A2', localization['monday'])
        worksheet.write('A3', localization['tuesday'])
        worksheet.write('A4', localization['wednesday'])
        worksheet.write('A5', localization['thursday'])
        worksheet.write('A6', localization['friday'])
        worksheet.write('A7', localization['saturday'])
        worksheet.write('A8', localization['sunday'])
        for i in range(len(bookings_per_day)):
            worksheet.write('B'+str(i+2), bookings_per_day[i])

        chart.add_series({
            'name': localization['number_of_visits'],
            'categories': '=Sheet1!$A$2:$A$8',
            'values': '=Sheet1!$B$2:$B$8'})

        chart.set_title({'name': localization['dynamics_of_visits_by_days_of_the_week']})

        worksheet.insert_chart('C12', chart)

        workbook.close()

        check_token()
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}

        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={
                    "file": (secure_file_name, open(Path(str(Path.cwd()) + "/" + secure_file_name), "rb"),
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers=headers,
            )
        except requests.exceptions.RequestException:
            return {"message": "Error occurred during file upload"}, 500

        response_dict = orjson.loads(response.text)
        file_attrs = {
            "path": FILES_HOST + str(response_dict.get("path")),
            "title": secure_file_name,
            "size": Path(str(Path.cwd()) + "/" + secure_file_name).stat().st_size
        }

        if response_dict.get("thumb"):
            file_attrs['thumb'] = FILES_HOST + str(response_dict.get("thumb"))

        file_storage_object = File(**file_attrs)
        file_storage_object.save()

        Path(str(Path.cwd()) + "/" + secure_file_name).unlink()
        try:
            Path(str(Path.cwd()) + "/" + secure_file_name.replace('.xlsx', '.html')).unlink()
            Path(str(Path.cwd()) + "/" + secure_file_name.replace('.xlsx', '.pdf')).unlink()
        except FileNotFoundError:
            pass

        return file_storage_object


class AdminMeetingGroupBookingSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True)
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=Account.objects.all(), required=True)
    guests = serializers.ListField(child=serializers.JSONField(), allow_empty=True, required=False)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'author', 'date_to', 'date_from', 'users', 'room', 'guests']

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
                    message = f"Здравствуйте, {guest_name}. Вы были приглашены на встречу, " \
                              f"которая пройдёт в {attrs['room'].floor.office.title}, " \
                              f"этаж {attrs['room'].floor.title}, кабинет {attrs['room'].title}. " \
                              f"Дата и время проведения {datetime.strftime(message_date_from, '%d.%m.%Y %H:%M')}-" \
                              f"{datetime.strftime(message_date_to, '%H:%M')}"
                    send_email.delay(email=contact_data, subject="Встреча", message=message)
                except ValErr:
                    try:
                        contact_data = User.normalize_phone(contact_data)
                        message = f"Здравствуйте, {guest_name}. Вы были приглашены на встречу, " \
                                  f"которая пройдёт в {attrs['room'].floor.office.title}, " \
                                  f"этаж {attrs['room'].floor.title}, кабинет {attrs['room'].title}. " \
                                  f"Дата и время проведения {datetime.strftime(message_date_from, '%d.%m.%Y %H:%M')}-" \
                                  f"{datetime.strftime(message_date_to, '%H:%M')}"
                        send_sms.delay(phone_number=contact_data, message=message)
                    except ValueError:
                        raise ResponseException("Wrong format of email or phone",
                                                status_code=status.HTTP_400_BAD_REQUEST)
        return attrs

    @atomic()
    def group_create_meeting(self, context):
        group_booking = GroupBooking.objects.create(author=self.validated_data['author'],
                                                    guests=self.validated_data.get('guests'))

        date_activate_until = calculate_date_activate_until(self.validated_data['date_from'],
                                                            self.validated_data['date_to'])
        for user in self.validated_data['users']:
            b = Booking(user=user,
                        table=self.validated_data['room'].tables.all()[0],
                        date_to=self.validated_data['date_to'],
                        date_from=self.validated_data['date_from'],
                        date_activate_until=date_activate_until,
                        group_booking=group_booking)
            b.save()

        return AdminGroupBookingSerializer(instance=group_booking).data


class AdminWorkplaceGroupBookingSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True)
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=Account.objects.all(), required=True)
    tables = serializers.PrimaryKeyRelatedField(many=True, queryset=Table.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'author', 'date_to', 'date_from', 'users', 'tables']

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
        group_booking = GroupBooking.objects.create(author=self.validated_data['author'])

        date_activate_until = calculate_date_activate_until(self.validated_data['date_from'],
                                                            self.validated_data['date_to'])

        for i in range(len(self.validated_data['users'])):
            b = Booking(user=self.validated_data['users'][i],
                        table=self.validated_data['tables'][i],
                        date_to=self.validated_data['date_to'],
                        date_from=self.validated_data['date_from'],
                        date_activate_until=date_activate_until,
                        group_booking=group_booking)
            b.save()

        return AdminGroupWorkspaceSerializer(instance=group_booking).data
