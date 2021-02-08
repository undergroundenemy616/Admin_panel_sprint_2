from booking_api_django_new.settings import (FILES_HOST, FILES_PASSWORD,
                                             FILES_USERNAME, MEDIA_ROOT,
                                             MEDIA_URL)
from calendar import monthrange
from collections import Counter
from datetime import datetime, timezone, timedelta, date
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
import os
from pathlib import Path
import requests
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, UpdateModelMixin)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from time import strptime
import ujson
import uuid
from workalendar.europe import Russia
import xlsxwriter


from bookings.models import Booking
from bookings.serializers import (BookingActivateActionSerializer,
                                  BookingDeactivateActionSerializer,
                                  BookingFastSerializer, BookingListSerializer,
                                  BookingListTablesSerializer,
                                  BookingPersonalSerializer, BookingSerializer,
                                  BookingSlotsSerializer,
                                  SwaggerBookListActiveParametrs,
                                  SwaggerBookListTableParametrs,
                                  SwaggerBookListRoomTypeStats,
                                  SwaggerBookingEmployeeStatistics)
from core.pagination import DefaultPagination, LimitStartPagination
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from files.models import File
from files.serializers import BaseFileSerializer
from tables.serializers import Table, TableSerializer
from users.models import Account
from users.serializers import AccountSerializer


class BookingsView(GenericAPIView,
                   CreateModelMixin,
                   ListModelMixin,
                   DestroyModelMixin):
    """
    Book table, get information about specific booking.
    Methods available: GET, POST
    GET: Return information about one booking according to requested ID
     Params - :id:: booking id information about want to get
    POST: Create booking on requested table if it not overflowed
     Params - :date_from: - booking start datetime
              :date_to: - booking end datetime
              :table: - seat that need to be book
              :Theme: - Used only when booking table in room.room_type.unified=True, else used default value
    """
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):  # TODO CHECK maybe not work
        if self.request.method == 'DELETE':
            self.permission_classes = (IsAdmin, )
        return super(BookingsView, self).get_permissions()  # TODO: Not working

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.account.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        # TODO: Add addition not required "?id=" parameter for user id
        return self.list(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
        # TODO Check working and stability


class BookingsAdminView(BookingsView):
    """
    Admin route. Create Booking for any user.
    """
    permission_classes = (IsAdmin,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActionCheckAvailableSlotsView(GenericAPIView):
    serializer_class = BookingSlotsSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActionActivateBookingsView(GenericAPIView):
    """
    Authenticated User route. Change status of booking.
    """
    serializer_class = BookingActivateActionSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # request.data['user'] = request.user
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionDeactivateBookingsView(GenericAPIView):
    """
    Admin route. Deactivates any booking
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin, )

    def post(self, request, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionEndBookingsView(GenericAPIView, DestroyModelMixin):
    """
    User route. Deactivate booking only connected with User
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        if now < serializer.data["date_from"] and now < serializer.data["date_to"]:
            return self.destroy(request, *args, **kwargs)
        serializer.save(user=request.user)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionCancelBookingsView(GenericAPIView, DestroyModelMixin):
    """
    User route. Delete booking object from DB
    """
    queryset = Booking.objects.all().prefetch_related('user')
    permission_classes = (IsAuthenticated, )

    def delete(self, request, pk=None, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=pk)
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return self.destroy(request, *args, **kwargs)


class CreateFastBookingsView(GenericAPIView):
    """
    Admin route. Fast booking for any user.
    """
    serializer_class = BookingFastSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.account.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FastBookingAdminView(CreateFastBookingsView):
    permission_classes = (IsAdmin,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingListTablesView(GenericAPIView, ListModelMixin):
    """
    All User route. Show booking history of any requested table.
    Can be filtered by date_from-date_to.
    """
    serializer_class = BookingListTablesSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerBookListTableParametrs)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('date_from') and request.query_params.get('date_to'):
            table_instance = get_object_or_404(Table, pk=request.query_params.get('table'))
            serializer = self.serializer_class(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            queryset = self.queryset.is_overflowed_with_data(table=table_instance.id,
                                                             date_from=serializer.data['date_from'],
                                                             date_to=serializer.data['date_to'])
            response = {
                'id': table_instance.id,
                'table': TableSerializer(instance=table_instance).data,
                'floor': table_instance.room.floor.title,
                'room': table_instance.room.title,
                'history': [BookingSerializer(instance=book).data for book in queryset]
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            table_instance = get_object_or_404(Table, pk=request.query_params.get('table'))
            queryset = self.queryset.filter(table=table_instance.id)
            response = {
                'id': table_instance.id,
                'table': TableSerializer(instance=table_instance).data,
                'floor': table_instance.room.floor.title,
                'room': table_instance.room.title,
                'history': [BookingSerializer(instance=book).data for book in queryset]
            }
            return Response(response, status=status.HTTP_200_OK)


class BookingListPersonalView(GenericAPIView, ListModelMixin):
    """
    All User route. Shows all bookings that User have.
    Can be filtered by: date,
    """
    serializer_class = BookingPersonalSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [SearchFilter, ]
    search_fields = ['table__title',
                     'table__room__title',
                     'table__room__type__title',
                     'table__room__floor__office__title',
                     'table__room__floor__office__description']
    pagination_class = LimitStartPagination

    @swagger_auto_schema(query_serializer=BookingPersonalSerializer)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('search'):
            self.serializer_class = BookingSerializer
            return self.list(request, *args, **kwargs)
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        date_from = datetime.strptime(request.query_params.get('date_from'), '%Y-%m-%dT%H:%M:%S.%f')
        date_to = datetime.strptime(request.query_params.get('date_to'), '%Y-%m-%dT%H:%M:%S.%f')
        is_over = bool(serializer.data['is_over']) if serializer.data.get('is_over') else 0
        req_booking = self.queryset.filter(user=request.user.account.id).filter(
            Q(is_over=is_over),
            Q(date_from__gte=date_from, date_from__lt=date_to)
            | Q(date_from__lte=date_from, date_to__gte=date_to)
            | Q(date_to__gt=date_from, date_to__lte=date_to))
        self.queryset = req_booking
        self.serializer_class = BookingSerializer
        return self.list(request, *args, **kwargs)


class BookingsListUserView(BookingsAdminView):
    serializer_class = BookingListSerializer
    queryset = Booking.objects.all().prefetch_related('user')

    @swagger_auto_schema(query_serializer=SwaggerBookListActiveParametrs)
    def get(self, request, *args, **kwargs):
        account = get_object_or_404(Account, pk=request.query_params['user'])
        by_user = self.queryset.filter(user=account.id)
        self.queryset = by_user
        response = self.list(request, *args, **kwargs)
        response.data['user'] = AccountSerializer(instance=account).data
        return response


class BookingStatisticsRoomTypes(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerBookListRoomTypeStats)
    def get(self, request, *args, **kwargs):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        file_name = "From_" + date_from + "_To_" + date_to + ".xlsx"
        secure_file_name = uuid.uuid4().hex + file_name

        stats = self.queryset.all().raw(f"""
        SELECT b.id, rtr.title, rtr.office_id, b.date_from, b.date_to
        FROM bookings_booking b
        INNER JOIN tables_table t ON t.id = b.table_id
        INNER JOIN rooms_room rr on t.room_id = rr.id
        INNER JOIN room_types_roomtype rtr on rr.type_id = rtr.id
        where (b.date_from::date >= '{date_from}' and b.date_from::date < '{date_to}') or 
        (b.date_from::date <= '{date_from}' and b.date_to::date >= '{date_to}') or
        (b.date_to::date > '{date_from}' and b.date_to::date <= '{date_to}')""")
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

        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={"file": (secure_file_name, open(Path(str(Path.cwd()) + "/" + secure_file_name), "rb"),
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                auth=(FILES_USERNAME, FILES_PASSWORD),
            )
        except requests.exceptions.RequestException:
            return {"message": "Error occured during file upload"}, 500

        response_dict = ujson.loads(response.text)
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


class BookingEmployeeStatistics(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerBookingEmployeeStatistics)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('month'):
            month = request.query_params.get('month')
            month_num = int(strptime(month, '%B').tm_mon)
        else:
            month_num = int(datetime.now().month)
            month = datetime.now().strftime("%B")

        if request.query_params.get('year'):
            year = int(request.query_params.get('year'))
        else:
            year = int(datetime.now().year)

        file_name = month + '_' + str(year) + '.xlsx'
        secure_file_name = uuid.uuid4().hex + file_name

        stats = self.queryset.all().raw(f"""
        SELECT b.id, tt.id as table_id, tt.title as table_title, b.date_from, b.date_to, oo.id as office_id,
        oo.title as office_title, ff.title as floor_title, ua.id as user_id, ua.first_name as first_name,
        ua.middle_name as middle_name, ua.last_name as last_name
        FROM bookings_booking b
        INNER JOIN tables_table tt on b.table_id = tt.id
        INNER JOIN rooms_room rr on rr.id = tt.room_id
        INNER JOIN floors_floor ff on rr.floor_id = ff.id
        INNER JOIN offices_office oo on ff.office_id = oo.id
        INNER JOIN users_account ua on b.user_id = ua.id
        WHERE EXTRACT(MONTH from b.date_from) = {month_num} and EXTRACT(YEAR from b.date_from) = {year}""")

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
                    'office_title': stat['office_title'],
                    'office_id': stat['office_id'],
                    'book_count': 0,
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
                        employee['time'] = employee['time'] + int(
                            datetime.fromisoformat(result['date_to']).timestamp() -
                            datetime.fromisoformat(result['date_from']).timestamp())
                        employee['places'].append(str(result['table_id']))
                employee['middle_time'] = str(chop_microseconds(timedelta(days=0,
                                                                          seconds=employee['time'] / working_days)))
                employee['middle_booking_time'] = str(chop_microseconds(
                    timedelta(days=0, seconds=employee['time'] / employee['book_count'])))
                employee['time'] = str(chop_microseconds(timedelta(days=0, seconds=employee['time'])))

            set_rows = set()

            for employee in employees:
                set_rows.add(ujson.dumps(employee, sort_keys=True))

            list_rows = []

            for set_row in set_rows:
                list_rows.append(ujson.loads(set_row))

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
                    worksheet.write('B1', 'Среднее время брони в день (в часах)')
                    worksheet.write('C1', 'Общее время бронирования за месяц (в часах)')
                    worksheet.write('D1', 'Средняя длительность бронирования (в часах)')
                    worksheet.write('E1', 'Кол-во бронирований')
                    worksheet.write('F1', 'Офис')
                    worksheet.write('G1', 'Часто бронируемое место')
                else:
                    full_name = str(str(list_rows[j].get('last_name')) + ' ' +
                                    str(list_rows[j].get('first_name')) + ' ' +
                                    str(list_rows[j].get('middle_name'))).replace('None', "")
                    if not full_name.replace(" ", ""):
                        full_name = "Имя не указано"
                    worksheet.write('A' + str(i), full_name)
                    worksheet.write('B' + str(i), list_rows[j]['middle_time'])
                    worksheet.write('C' + str(i), list_rows[j]['time'])
                    worksheet.write('D' + str(i), list_rows[j]['middle_booking_time'])
                    worksheet.write('E' + str(i), list_rows[j]['book_count'])
                    worksheet.write('F' + str(i), list_rows[j]['office_title'])
                    worksheet.write('G' + str(i), list_rows[j]['table'])
                    j += 1

            worksheet.write('A' + str(len(list_rows) + 2), 'Рабочих дней в месяце:', bold)
            worksheet.write('B' + str(len(list_rows) + 2), working_days, bold)

            workbook.close()
        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={"file": (secure_file_name, open(Path(str(Path.cwd()) + "/" + secure_file_name), "rb"),
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                auth=(FILES_USERNAME, FILES_PASSWORD),
            )
        except requests.exceptions.RequestException:
            return {"message": "Error occured during file upload"}, 500

        response_dict = ujson.loads(response.text)
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


def room_type_statictic_serializer(stats):
    return {
        "booking_id": str(stats.id),
        "room_type_title": stats.title,
        "office_id": str(stats.office_id)
    }


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
        "date_to": str(stats.date_to)
    }


def most_frequent(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)
