from booking_api_django_new.settings import FILES_HOST
from calendar import monthrange
from core.handlers import ResponseException
from datetime import datetime, timedelta, date
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
import pandas as pd
from pathlib import Path
import pdfkit
import requests
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from time import strptime
import orjson
import os
import uuid
from workalendar.europe import Russia
import xlsxwriter


from bookings.models import Booking
from bookings.serializers import (BookingSerializer,
                                  SwaggerBookListRoomTypeStats,
                                  SwaggerBookingEmployeeStatistics,
                                  SwaggerBookingFuture,
                                  SwaggerDashboard,
                                  StatisticsSerializer,
                                  get_duration, room_type_statictic_serializer,
                                  employee_statistics, most_frequent, bookings_future, date_validation, months_between)
from core.permissions import IsAdmin
from files.models import File
from files.serializers import BaseFileSerializer, check_token
from tables.serializers import Table, TableMarker
from users.models import Account


class BookingStatisticsRoomTypes(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerBookListRoomTypeStats)
    def get(self, request, *args, **kwargs):
        serializer = StatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        date_validation(serializer.data.get('date_from'))
        date_validation(serializer.data.get('date_to'))
        date_from = serializer.data.get('date_from')
        date_to = serializer.data.get('date_to')
        doc_format = serializer.data.get('doc_format')

        file_name = "From_" + date_from + "_To_" + date_to + ".xlsx"
        secure_file_name = uuid.uuid4().hex + file_name

        query = f"""
        SELECT b.id, rtr.title, rtr.office_id, b.date_from, b.date_to, b.status
        FROM bookings_booking b
        INNER JOIN tables_table t ON t.id = b.table_id
        INNER JOIN rooms_room rr ON t.room_id = rr.id
        INNER JOIN room_types_roomtype rtr on rr.type_id = rtr.id
        WHERE ((b.date_from::date >= '{date_from}' and b.date_from::date < '{date_to}') or
        (b.date_from::date <= '{date_from}' and b.date_to::date >= '{date_to}') or
        (b.date_to::date > '{date_from}' and b.date_to::date <= '{date_to}')) and b.status = 'over'"""

        if serializer.data.get('office_id'):
            query = query + f""" and rtr.office_id = '{serializer.data.get('office_id')}'"""

        stats = self.queryset.all().raw(query)
        sql_results = []
        set_of_types = set()
        list_of_types = []
        for s in stats:
            set_of_types.add(s.title)
            list_of_types.append(s.title)
            sql_results.append(room_type_statictic_serializer(s))
        number_of_types = len(set_of_types)
        counts = {}
        for i in list_of_types:
            counts[i] = counts.get(i, 0) + 1
        if sql_results:
            workbook = xlsxwriter.Workbook(secure_file_name)

            worksheet = workbook.add_worksheet()
            bold = workbook.add_format({'bold': 1})

            j = 0

            for i in range(len(set_of_types) + 1):
                i += 1
                if i == 1:
                    worksheet.write('A1', 'Тип комнаты')
                    worksheet.write('B1', 'Число бронирований комнат такого типа')
                else:
                    worksheet.write('A' + str(i), list(set_of_types)[j])
                    worksheet.write('B' + str(i), counts.get(list(set_of_types)[j]))
                    j += 1

            worksheet.write('A' + str(number_of_types + 2), 'Общее число бронирований:', bold)
            worksheet.write('B' + str(number_of_types + 2), len(sql_results), bold)

            chart = workbook.add_chart({'type': 'pie'})

            chart.add_series({
                'name': 'Распределение бронирований мест по типам (%)',
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
                                                                     secure_file_name.replace('.xlsx', '.pdf')), "rb"),
                                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                            headers=headers,
                        )
                    except requests.exceptions.RequestException:
                        return {"message": "Error occured during file upload"}, 500
                elif doc_format == 'xlsx':
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
                "title": secure_file_name if doc_format == 'xlsx' else secure_file_name.replace('.xlsx', '.pdf'),
                "size": Path(str(Path.cwd()) + "/" + secure_file_name).stat().st_size if
                doc_format == 'xlsx' else
                Path(str(Path.cwd()) + "/" + secure_file_name.replace('.xlsx', '.pdf')).stat().st_size,
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

            return Response(BaseFileSerializer(instance=file_storage_object).data, status=status.HTTP_201_CREATED)
        else:
            return Response("Data not found", status=status.HTTP_404_NOT_FOUND)


class BookingEmployeeStatistics(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerBookingEmployeeStatistics)
    def get(self, request, *args, **kwargs):
        serializer = StatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if len(serializer.data.get('month')) > 10 or \
                int(serializer.data.get('year')) not in range(1970, 2500):
            return ResponseException("Wrong data")
        if serializer.data.get('month'):
            month = serializer.data.get('month')
            month_num = int(strptime(month, '%B').tm_mon)
        else:
            month_num = int(datetime.now().month)
            month = datetime.now().strftime("%B")

        if serializer.data.get('year'):
            year = int(serializer.data.get('year'))
        else:
            year = int(datetime.now().year)

        file_name = month + '_' + str(year) + '.xlsx'
        secure_file_name = uuid.uuid4().hex + file_name

        query = f"""
        SELECT b.id, tt.id as table_id, tt.title as table_title, b.date_from, b.date_to, oo.id as office_id,
        oo.title as office_title, ff.title as floor_title, b.user_id as user_id, ua.first_name as first_name,
        ua.middle_name as middle_name, ua.last_name as last_name, ua.phone_number as phone_number, b.status
        FROM bookings_booking b
        JOIN tables_table tt on b.table_id = tt.id
        JOIN rooms_room rr on rr.id = tt.room_id
        JOIN floors_floor ff on rr.floor_id = ff.id
        JOIN offices_office oo on ff.office_id = oo.id
        JOIN users_account ua on b.user_id = ua.id
        WHERE EXTRACT(MONTH from b.date_from) = {month_num} and EXTRACT(YEAR from b.date_from) = {year} 
        and (b.status='over' or b.status = 'canceled' or b.status = 'auto_canceled')"""

        if serializer.data.get('office_id'):
            query = query + f""" and oo.id = '{serializer.data.get('office_id')}'"""

        stats = self.queryset.all().raw(query)

        sql_results = []

        for s in stats:
            sql_results.append(employee_statistics(s))

        if sql_results:
            employees = []
            for stat in sql_results:
                employees.append({
                    'id': stat['user_id'],
                    'first_name': stat['first_name'],
                    'middle_name': stat['middle_name'],
                    'last_name': stat['last_name'],
                    'phone_number': stat['phone_number'],
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
                    worksheet.write('B' + str(i), list_rows[j]['phone_number'] if list_rows[j]['phone_number'] != 'None' else 'Не указан')
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

            return Response(BaseFileSerializer(instance=file_storage_object).data, status=status.HTTP_201_CREATED)
        else:
            return Response("Data not found", status=status.HTTP_404_NOT_FOUND)



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
