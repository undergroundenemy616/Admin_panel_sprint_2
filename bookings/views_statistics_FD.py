from booking_api_django_new.filestorage_auth import check_token
from booking_api_django_new.settings import FILES_HOST
from calendar import monthrange
from core.handlers import ResponseException
from datetime import datetime, timedelta, date
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from pathlib import Path
import requests
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
import orjson
import os
import uuid
from workalendar.europe import Russia
import xlsxwriter


from bookings.models import Booking
from bookings.serializers import (BookingSerializer,
                                  SwaggerBookingFuture,
                                  SwaggerDashboard,
                                  StatisticsSerializer,
                                  bookings_future, date_validation, months_between)
from core.permissions import IsAdmin
from files.models import File
from files.serializers import BaseFileSerializer
from tables.serializers import Table, TableMarker
from users.models import Account


class BookingFuture(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerBookingFuture)
    def get(self, request, *args, **kwargs):
        serializer = StatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        date_validation(serializer.data.get('date'))
        date = serializer.data.get('date')

        file_name = "future_" + date + '.xlsx'

        query = f"""
        SELECT b.id, b.user_id as user_id, ua.first_name as first_name, ua.middle_name as middle_name,
        ua.last_name as last_name, ua.phone_number as phone_number, oo.id as office_id, oo.title as office_title, 
        ff.id as floor_id, ff.title as floor_title, tt.id as table_id, tt.title as table_title, b.date_from, b.date_to,
        b.date_activate_until, b.status
        FROM bookings_booking b
        JOIN tables_table tt on b.table_id = tt.id
        JOIN rooms_room rr on rr.id = tt.room_id
        JOIN floors_floor ff on rr.floor_id = ff.id
        JOIN offices_office oo on ff.office_id = oo.id
        JOIN users_account ua on b.user_id = ua.id
        WHERE b.date_from::date = '{date}' and (b.status = 'waiting' or b.status = 'active')"""

        if serializer.data.get('office_id'):
            query = query + f""" and oo.id = '{serializer.data.get('office_id')}'"""

        stats = self.queryset.all().raw(query)

        sql_results = []

        for s in stats:
            sql_results.append(bookings_future(s))

        if sql_results:
            secure_file_name = uuid.uuid4().hex + file_name

            workbook = xlsxwriter.Workbook(secure_file_name)

            worksheet = workbook.add_worksheet()

            j = 0

            for i in range(len(sql_results) + 1):
                i += 1
                if i == 1:
                    worksheet.write('A1', 'Ф.И.О')
                    worksheet.write('B1', 'Тел. номер')
                    worksheet.write('C1', 'Начало брони')
                    worksheet.write('D1', 'Окончание брони')
                    worksheet.write('E1', 'Продолжительность брони (в часах)')
                    worksheet.write('F1', 'Офис')
                    worksheet.write('G1', 'Этаж')
                    worksheet.write('H1', 'Рабочее место')
                else:
                    full_name = str(str(sql_results[j].get('last_name')) + ' ' +
                                    str(sql_results[j].get('first_name')) + ' ' +
                                    str(sql_results[j].get('middle_name'))).replace('None', "")
                    if not full_name.replace(" ", ""):
                        full_name = "Имя не указано"
                    book_time = float((datetime.fromisoformat(sql_results[j]['date_to']).timestamp() -
                                       datetime.fromisoformat(sql_results[j]['date_from']).timestamp()) / 3600).__round__(2)

                    try:
                        r_date_from = datetime.strptime(sql_results[j]['date_from'].replace("T", " ").split("+")[0],
                                                        '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
                        r_date_to = datetime.strptime(sql_results[j]['date_to'].replace("T", " ").split("+")[0],
                                                      '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
                    except ValueError:
                        correct_date_from = sql_results[j]['date_from'].replace("T", " ").split(".")[0]
                        correct_date_to = sql_results[j]['date_from'].replace("T", " ").split(".")[0]
                        r_date_from = datetime.strptime(correct_date_from.replace("T", " ").split("+")[0],
                                                        '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
                        r_date_to = datetime.strptime(correct_date_to.replace("T", " ").split("+")[0],
                                                      '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)

                    worksheet.write('A' + str(i), full_name)
                    worksheet.write('B' + str(i), sql_results[j]['phone_number'] if sql_results[j]['phone_number'] != 'None' else 'Не указан')
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

            return Response(BaseFileSerializer(instance=file_storage_object).data, status=status.HTTP_201_CREATED)
        else:
            return Response("Data not found", status=status.HTTP_404_NOT_FOUND)


class BookingStatisticsDashboard(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerDashboard)
    def get(self, request, *args, **kwargs):
        serializer = StatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        valid_office_id = None
        if serializer.data.get('office_id'):
            try:
                valid_office_id = uuid.UUID(serializer.data.get('office_id')).hex
            except ValueError:
                raise ResponseException("Office ID is not valid", status.HTTP_400_BAD_REQUEST)
        if serializer.data.get('date_from') and serializer.data.get('date_to'):
            date_validation(serializer.data.get('date_from'))
            date_validation(serializer.data.get('date_to'))
            date_from = serializer.data.get('date_from')
            date_to = serializer.data.get('date_to')
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
            number_of_bookings = self.queryset.filter(Q(table__room__floor__office_id=valid_office_id) &
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
            number_of_activated_bookings = self.queryset.filter(Q(status__in=['active', 'over']) &
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
            bookings_with_hours = self.queryset.raw(f"""SELECT 
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
            tables_from_booking = self.queryset.filter(Q(table__room__floor__office_id=valid_office_id) &
                                                       Q(table__room__type__is_deletable=False) &
                                                       Q(table__room__type__bookable=True)).only('table_id')
        else:
            all_tables = Table.objects.filter(Q(room__type__is_deletable=False) &
                                              Q(room__type__bookable=True) &
                                              Q(room__type__unified=False))
            tables_with_markers = TableMarker.objects.filter(Q(table__room__type__is_deletable=False) &
                                                             Q(table__room__type__bookable=True)).count()
            number_of_bookings = self.queryset.filter((Q(date_from__date__gte=date_from) &
                                                       Q(date_from__date__lt=date_to))
                                                      |
                                                      (Q(date_from__date__lte=date_from) &
                                                       Q(date_to__date__gte=date_to))
                                                      |
                                                      (Q(date_to__date__gt=date_from) &
                                                       Q(date_to__date__lte=date_to))).count()
            number_of_activated_bookings = self.queryset.filter(status__in=['active', 'over']).count()
            bookings_with_hours = self.queryset.raw(f"""SELECT 
                        DATE_PART('day', b.date_to::timestamp - b.date_from::timestamp) * 24 +
                        DATE_PART('hour', b.date_to::timestamp - b.date_from::timestamp) as hours, b.id from bookings_booking b
                        WHERE (b.date_from::date >= '{date_from}' and b.date_from::date < '{date_to}') or 
                        (b.date_from::date <= '{date_from}' and b.date_to::date >= '{date_to}') or
                        (b.date_to::date > '{date_from}' and b.date_to::date <= '{date_to}')""")
            tables_from_booking = self.queryset.filter(Q(table__room__type__is_deletable=False) &
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

        return Response(orjson.loads(orjson.dumps(response)), status=status.HTTP_200_OK)
