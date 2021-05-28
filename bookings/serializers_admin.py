import os
import uuid
from calendar import monthrange
from collections import Counter
from datetime import datetime, timedelta, date

import xlsxwriter
import orjson
import requests
from django.db.models import Q
from django.db.transaction import atomic
from rest_framework import serializers, status
from workalendar.europe import Russia

from pathlib import Path
from time import strptime
from booking_api_django_new.settings import FILES_HOST
from bookings.models import Booking
from core.handlers import ResponseException
from files.serializers_admin import check_token
from files.models import File
from room_types.models import RoomType
from tables.models import Table, TableMarker
from users.models import Account


def employee_statistics(stats):
    return {
        "booking_id": str(stats.id),
        "table_id": str(stats.table_id),
        "table_title": stats.table_title,
        "office_id": str(stats.office_id),
        "office_title": stats.office_title,
        "floor_title": stats.floor_title,
        "user_id": str(stats.user_id),
        "first_name": stats.first_name,
        "middle_name": stats.middle_name,
        "last_name": stats.last_name,
        "date_from": str(stats.date_from),
        "date_to": str(stats.date_to),
        "phone_number1": str(stats.phone_number1),
        "phone_number2": str(stats.phone_number2),
        "book_status": str(stats.status)
    }


def get_duration(duration):
    hours = int(duration / 3600)
    minutes = int(duration % 3600 / 60)
    seconds = int((duration % 3600) % 60)
    return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


def most_frequent(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


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


class AdminSwaggerBookingEmployee(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    month = serializers.CharField(required=False, max_length=10)
    year = serializers.IntegerField(required=False, max_value=2500, min_value=1970)
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

        query = f"""
        SELECT b.id, tt.id as table_id, tt.title as table_title, b.date_from, b.date_to, oo.id as office_id,
        oo.title as office_title, ff.title as floor_title, b.user_id as user_id, ua.first_name as first_name,
        ua.middle_name as middle_name, ua.last_name as last_name, uu.phone_number as phone_number1,
        ua.phone_number as phone_number2, b.status
        FROM bookings_booking b
        JOIN tables_table tt on b.table_id = tt.id
        JOIN rooms_room rr on rr.id = tt.room_id
        JOIN floors_floor ff on rr.floor_id = ff.id
        JOIN offices_office oo on ff.office_id = oo.id
        JOIN users_account ua on b.user_id = ua.id
        JOIN users_user uu on ua.user_id = uu.id
        WHERE EXTRACT(MONTH from b.date_from) = {month_num} and EXTRACT(YEAR from b.date_from) = {year}
        and (b.status='over' or b.status = 'canceled' or b.status = 'auto_canceled')"""

        if self.data.get('office_id'):
            query = query + f""" and oo.id = '{self.data.get('office_id')}'"""

        stats = Booking.objects.all().raw(query)

        sql_results = []

        for s in stats:
            sql_results.append(employee_statistics(s))

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
                    if result['book_status'] == 'over':
                        employee['over_book'] = employee['over_book'] + 1
                    elif result['book_status'] == 'canceled':
                        employee['canceled_book'] = employee['canceled_book'] + 1
                    elif result['book_status'] == 'auto_canceled':
                        employee['auto_canceled_book'] = employee['auto_canceled_book'] + 1
                    employee['time'] = employee['time'] + int(
                        datetime.fromisoformat(result['date_to']).timestamp() -
                        datetime.fromisoformat(result['date_from']).timestamp())
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

        for i in range(len(list_rows) + 1):
            i += 1
            if i == 1:
                worksheet.write('A1', 'Ф.И.О')
                worksheet.write('B1', 'Тел. номер')
                worksheet.write('C1', 'Среднее время брони в день (в часах)')
                worksheet.write('D1', 'Общее время бронирования за месяц (в часах)')
                worksheet.write('E1', 'Средняя длительность бронирования (в часах)')
                worksheet.write('F1', 'Кол-во бронирований')
                worksheet.write('G1', 'Кол-во завершенных бронирований')
                worksheet.write('H1', 'Кол-во отмененных бронирований')
                worksheet.write('I1', 'Кол-во бронирований отмененных автоматически')
                worksheet.write('J1', 'Офис')
                worksheet.write('K1', 'Часто бронируемое место')
            else:
                full_name = str(str(list_rows[j].get('last_name')) + ' ' +
                                str(list_rows[j].get('first_name')) + ' ' +
                                str(list_rows[j].get('middle_name'))).replace('None', "")
                if not full_name.replace(" ", ""):
                    full_name = "Имя не указано"
                worksheet.write('A' + str(i), full_name)
                worksheet.write('B' + str(i), list_rows[j]['phone_number'] if list_rows[j][
                                                                                  'phone_number'] != 'None' else 'Не указан')
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

        worksheet.write('A' + str(len(list_rows) + 2), 'Рабочих дней в месяце:', bold)
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
            return {"message": "Error occured during file upload"}, 500

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
