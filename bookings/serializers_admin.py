import uuid
from calendar import monthrange
from datetime import datetime, date

from django.db.models import Q
from django.db.transaction import atomic
from rest_framework import serializers, status
from workalendar.europe import Russia

from bookings.models import Booking
from core.handlers import ResponseException
from room_types.models import RoomType
from tables.models import Table, TableMarker
from users.models import Account


def date_validation(date):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
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


class AdminSwaggerDashboard(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=False, format='%Y-%m-%d')
    date_to = serializers.DateField(required=False, format='%Y-%m-%d')


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
                                                      )
                                                      ).count()
            number_of_activated_bookings = bookings.filter(Q(status__in=['active', 'over']) &
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
                                                                )
                                                                ).count()
            bookings_with_hours = bookings.raw(f"""SELECT 
                    DATE_PART('day', b.date_to::timestamp - b.date_from::timestamp) * 24 +
                    DATE_PART('hour', b.date_to::timestamp - b.date_from::timestamp) as hours, oo.id as office_id,
                    b.id from bookings_booking b
                    INNER JOIN tables_table tt on tt.id = b.table_id
                    INNER JOIN rooms_room rr on rr.id = tt.room_id
                    INNER JOIN floors_floor ff on ff.id = rr.floor_id
                    INNER JOIN offices_office oo on oo.id = ff.office_id
                    WHERE ((b.date_from::date >= '{date_from}' and b.date_from::date < '{date_to}') or
                    (b.date_from::date <= '{date_from}' and b.date_to::date >= '{date_to}') or
                    (b.date_to::date > '{date_from}' and b.date_to::date <= '{date_to}')) and 
                    office_id = '{valid_office_id}'""")
            tables_from_booking = bookings.filter(Q(table__room__floor__office_id=valid_office_id) &
                                                       Q(table__room__type__is_deletable=False) &
                                                       Q(table__room__type__bookable=True)).only('table_id')
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
            number_of_activated_bookings = bookings.filter(status__in=['active', 'over']).count()
            bookings_with_hours = bookings.raw(f"""SELECT 
                                DATE_PART('day', b.date_to::timestamp - b.date_from::timestamp) * 24 +
                                DATE_PART('hour', b.date_to::timestamp - b.date_from::timestamp) as hours, b.id from bookings_booking b
                                WHERE (b.date_from::date >= '{date_from}' and b.date_from::date < '{date_to}') or 
                                (b.date_from::date <= '{date_from}' and b.date_to::date >= '{date_to}') or
                                (b.date_to::date > '{date_from}' and b.date_to::date <= '{date_to}')""")
            tables_from_booking = bookings.filter(Q(table__room__type__is_deletable=False) &
                                                       Q(table__room__type__bookable=True)).only('table_id')
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

        tables_available_for_booking = all_tables.filter(is_occupied=False).count()
        active_users = all_accounts.count()
        total_tables = Table.objects.filter(room__floor__office_id=valid_office_id).count()

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
            sum_of_booking_hours += booking.hours

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

        response = {
            "tables_available_for_booking": tables_available_for_booking,
            "percentage_of_tables_available_for_booking": percentage_of_tables_available_for_booking.__round__(2),
            "active_users": active_users,
            "number_of_bookings": number_of_bookings,
            "percent_of_tables_booked_at_least_once": percent_of_tables_booked_at_least_once.__round__(2),
            "share_of_confirmed_bookings": share_of_confirmed_bookings.__round__(2),
            "recycling_percentage_for_all_workplaces": recycling_percentage_for_all_workplaces.__round__(2),
            "percentage_of_registered_tables": percentage_of_registered_tables.__round__(2)
        }

        return response
