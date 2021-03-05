from booking_api_django_new.settings import (FILES_HOST, FILES_PASSWORD, FILES_USERNAME)
from calendar import monthrange
from core.handlers import ResponseException
from datetime import datetime, timezone, timedelta, date
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from pathlib import Path
import pytz
import requests
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.response import Response
from time import strptime
import orjson
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
                                  SwaggerBookingEmployeeStatistics,
                                  SwaggerBookingFuture,
                                  SwaggerDashboard,
                                  get_duration, room_type_statictic_serializer,
                                  employee_statistics, most_frequent, bookings_future, date_validation, months_between)
from core.pagination import DefaultPagination, LimitStartPagination
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from files.models import File
from files.serializers import BaseFileSerializer
from tables.serializers import Table, TableSerializer, TableMarker
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
    queryset = Booking.objects.all().select_related('table')
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


class CreateFastBookingsView(GenericAPIView):
    """
    Admin route. Fast booking for any user.
    """
    serializer_class = BookingFastSerializer
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


class ActionCheckAvailableSlotsView(GenericAPIView):
    serializer_class = BookingSlotsSerializer
    queryset = Booking.objects.all().select_related('table')
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActionActivateBookingsView(GenericAPIView):
    """
    Authenticated User route. Change status of booking.
    """
    serializer_class = BookingActivateActionSerializer
    queryset = Booking.objects.all().select_related('table')
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
    queryset = Booking.objects.all().select_related('table')
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
    queryset = Booking.objects.all().select_related('table')
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        # now = datetime.utcnow().replace(tzinfo=timezone.utc)
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        # booking = serializer.validated_data['booking']
        # if now < booking.date_from and now < booking.date_to:
        #     return self.destroy(request, *args, **kwargs)
        serializer.save()
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionCancelBookingsView(GenericAPIView):
    """
    User route. Set booking over
    """
    queryset = Booking.objects.all().select_related('table', 'user')
    serializer_class = BookingDeactivateActionSerializer
    permission_classes = (IsAuthenticated, )

    def delete(self, request, pk=None, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=pk)
        user_is_admin = False
        for group in request.user.account.groups.all():
            if group.title == 'Администратор' and not group.is_deletable:
                user_is_admin = True
        if existing_booking.user.id != request.user.account.id and not user_is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)
        request.data['booking'] = existing_booking.id
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = get_object_or_404(Booking, pk=pk)
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)


class BookingListTablesView(GenericAPIView, ListModelMixin):
    """
    All User route. Show booking history of any requested table.
    Can be filtered by date_from-date_to.
    """
    serializer_class = BookingListTablesSerializer
    queryset = Booking.objects.all().select_related('table')
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
    queryset = Booking.objects.all().select_related('table', 'user').prefetch_related(
        'table__room__floor__office', 'table__room__type', 'table__room__zone', 'table__tags',
        'table__images', 'table__table_marker').order_by('-is_active', '-date_from')
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
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        date_from = datetime.strptime(request.query_params.get(
            'date_from', '0001-01-01T00:00:00.0'), '%Y-%m-%dT%H:%M:%S.%f')
        date_to = datetime.strptime(request.query_params.get(
            'date_to', '9999-12-12T12:59:59.9'), '%Y-%m-%dT%H:%M:%S.%f')
        is_over = bool(serializer.data['is_over']) if serializer.data.get('is_over') else 0
        if is_over == 1:
            req_booking = self.queryset.filter(user=request.user.account.id).filter(
                Q(status__in=['canceled', 'auto_canceled', 'over']),
                Q(date_from__gte=date_from, date_from__lt=date_to)
                | Q(date_from__lte=date_from, date_to__gte=date_to)
                | Q(date_to__gt=date_from, date_to__lte=date_to))
        else:
            req_booking = self.queryset.filter(user=request.user.account.id).filter(
                Q(status__in=['waiting', 'active']),
                Q(date_from__gte=date_from, date_from__lt=date_to)
                | Q(date_from__lte=date_from, date_to__gte=date_to)
                | Q(date_to__gt=date_from, date_to__lte=date_to))
        self.queryset = req_booking.order_by('-date_from')
        self.serializer_class = BookingSerializer
        return self.list(request, *args, **kwargs)


class BookingsListUserView(BookingsAdminView):
    serializer_class = BookingListSerializer
    queryset = Booking.objects.all().prefetch_related('user').select_related('table')

    @swagger_auto_schema(query_serializer=SwaggerBookListActiveParametrs)
    def get(self, request, *args, **kwargs):
        account = get_object_or_404(Account, pk=request.query_params['user'])
        by_user = self.queryset.filter(user=account.id, status__in=['waiting', 'active'])
        self.queryset = by_user
        response = self.list(request, *args, **kwargs)
        response.data['user'] = AccountSerializer(instance=account).data
        return response


class BookingStatisticsRoomTypes(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerBookListRoomTypeStats)
    def get(self, request, *args, **kwargs):
        date_validation(request.query_params.get('date_from'))
        date_validation(request.query_params.get('date_to'))
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        file_name = "From_" + date_from + "_To_" + date_to + ".xlsx"
        secure_file_name = uuid.uuid4().hex + file_name

        stats = self.queryset.all().raw(f"""
        SELECT b.id, rtr.title, rtr.office_id, b.date_from, b.date_to
        FROM bookings_booking b
        INNER JOIN tables_table t ON t.id = b.table_id
        INNER JOIN rooms_room rr ON t.room_id = rr.id
        INNER JOIN room_types_roomtype rtr on rr.type_id = rtr.id
        WHERE (b.date_from::date >= '{date_from}' and b.date_from::date < '{date_to}') or 
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


class BookingEmployeeStatistics(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerBookingEmployeeStatistics)
    def get(self, request, *args, **kwargs):
        if len(request.query_params.get('month')) > 10 or \
                int(request.query_params.get('year')) not in range(1970, 2500):
            return ResponseException("Wrong data")
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
                employee['middle_time'] = str(get_duration(
                    timedelta(days=0, seconds=employee['time'] / working_days).total_seconds()
                ))
                employee['middle_booking_time'] = str(get_duration(
                    timedelta(days=0, seconds=employee['time'] / employee['book_count']).total_seconds()))
                employee['time'] = str(get_duration(timedelta(days=0, seconds=employee['time']).total_seconds()))

            set_rows = set()

            for employee in employees:
                set_rows.add(orjson.dumps(employee, sort_keys=True))

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


class BookingFuture(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerBookingFuture)
    def get(self, request, *args, **kwargs):
        date_validation(request.query_params.get('date'))
        date = request.query_params.get('date')

        file_name = "future_" + date + '.xlsx'

        stats = self.queryset.all().raw(f"""
        SELECT b.id, ua.id as user_id, ua.first_name as first_name, ua.middle_name as middle_name, 
        ua.last_name as last_name, oo.id as office_id, oo.title as office_title, ff.id as floor_id, 
        ff.title as floor_title, tt.id as table_id, tt.title as table_title, b.date_from, b.date_to, 
        b.date_activate_until
        FROM bookings_booking b
        INNER JOIN tables_table tt on b.table_id = tt.id
        INNER JOIN rooms_room rr on rr.id = tt.room_id
        INNER JOIN floors_floor ff on rr.floor_id = ff.id
        INNER JOIN offices_office oo on ff.office_id = oo.id
        INNER JOIN users_account ua on b.user_id = ua.id
        WHERE b.date_from::date = '{date}'""")

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
                    worksheet.write('B1', 'Начало брони')
                    worksheet.write('C1', 'Окончание брони')
                    worksheet.write('D1', 'Продолжительность брони (в часах)')
                    worksheet.write('E1', 'Офис')
                    worksheet.write('F1', 'Этаж')
                    worksheet.write('G1', 'Рабочее место')
                else:
                    full_name = str(str(sql_results[j].get('last_name')) + ' ' +
                                    str(sql_results[j].get('first_name')) + ' ' +
                                    str(sql_results[j].get('middle_name'))).replace('None', "")
                    if not full_name.replace(" ", ""):
                        full_name = "Имя не указано"
                    book_time = float((datetime.fromisoformat(sql_results[j]['date_to']).timestamp() -
                                       datetime.fromisoformat(sql_results[j]['date_from']).timestamp()) / 3600).__round__(2)

                    r_date_from = datetime.strptime(sql_results[j]['date_from'].replace("T", " ").split("+")[0],
                                                    '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
                    r_date_to = datetime.strptime(sql_results[j]['date_to'].replace("T", " ").split("+")[0],
                                                  '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)

                    worksheet.write('A' + str(i), full_name)
                    worksheet.write('B' + str(i), str(r_date_from))
                    worksheet.write('C' + str(i), str(r_date_to))
                    worksheet.write('D' + str(i), book_time),
                    worksheet.write('E' + str(i), str(sql_results[j]['office_title'])),
                    worksheet.write('F' + str(i), sql_results[j]['floor_title']),
                    worksheet.write('G' + str(i), str(sql_results[j]['table_title']))
                    j += 1

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
            return Response("Not found", status=status.HTTP_404_NOT_FOUND)


class BookingStatisticsDashboard(GenericAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = (IsAdmin,)

    @swagger_auto_schema(query_serializer=SwaggerDashboard)
    def get(self, request, *args, **kwargs):
        valid_office_id = None
        if request.query_params.get('office_id'):
            try:
                valid_office_id = uuid.UUID(request.query_params.get('office_id')).hex
            except ValueError:
                raise ResponseException("Office ID is not valid", status.HTTP_400_BAD_REQUEST)
        if request.query_params.get('date_from') and request.query_params.get('date_to'):
            date_validation(request.query_params.get('date_from'))
            date_validation(request.query_params.get('date_to'))
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
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
