from collections import Counter
from datetime import datetime, timezone, timedelta, date
import tables
import time
import random

from rest_framework import serializers, status

from bookings.models import Booking, Table
from bookings.validators import BookingTimeValidator
from core.handlers import ResponseException
from core.pagination import DefaultPagination
from floors.models import Floor
from offices.models import Office
from room_types.models import RoomType
from rooms.models import Room
from users.models import Account, User


class SwaggerBookListActiveParametrs(serializers.Serializer):
    user = serializers.UUIDField()


class SwaggerBookListTableParametrs(serializers.Serializer):
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    table = serializers.UUIDField()


class SwaggerBookListRoomTypeStats(serializers.Serializer):
    date_from = serializers.DateField(required=True, format='%Y-%m-%d')
    date_to = serializers.DateField(required=True, format='%Y-%m-%d')


class SwaggerBookingEmployeeStatistics(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    month = serializers.CharField(required=False, max_length=10)
    year = serializers.IntegerField(required=False, max_value=2500, min_value=1970)


class SwaggerBookingFuture(serializers.Serializer):
    date = serializers.DateField(required=False, format='%Y-%m-%d')


class SwaggerDashboard(serializers.Serializer):
    office_id = serializers.UUIDField(required=False, format='hex_verbose')
    date_from = serializers.DateField(required=False, format='%Y-%m-%d')
    date_to = serializers.DateField(required=False, format='%Y-%m-%d')


class BaseBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        depth = 1


class BookingSerializer(serializers.ModelSerializer):
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
        response = BaseBookingSerializer(instance).data
        response['active'] = response['is_active']
        del response['is_active']
        response['table'] = tables.serializers.TableSerializer(instance=instance.table).data
        response['room'] = {"id": instance.table.room.id,
                            "title": instance.table.room.title,
                            "type": instance.table.room.type.title,
                            "zone": {"id": instance.table.room.zone.id,
                                     "title": instance.table.room.zone.title} if instance.table.room.zone else None
                            }
        response['floor'] = {"id": instance.table.room.floor.id,
                             "title": instance.table.room.floor.title}
        response['office'] = {"id": instance.table.room.floor.office.id,
                              "title": instance.table.room.floor.office.title}
        response['user'] = instance.user_id
        return response

    def create(self, validated_data, *args, **kwargs):
        # This is the hack to evade booking by two or more user on the same table in the same time
        time.sleep(random.uniform(0.001, 0.005))
        time.sleep(random.uniform(0.001, 0.003))
        time.sleep(random.uniform(0.01, 0.07))
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


class SlotsSerializer(serializers.Serializer):
    """Serialize and validate multiple booking time periods"""
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)

    class Meta:
        fields = ['date_from', 'date_to']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()


class BookingSlotsSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=False)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=False)
    slots = SlotsSerializer(many=True, required=True)
    tags = serializers.ListSerializer(child=serializers.CharField(), required=False)

    class Meta:
        model = Booking
        fields = ['floor', 'room', 'table', 'slots', 'tags']

    def create(self, validated_data, *args, **kwargs):
        """OMG: actually it's not create but 'GET available tables at this time periods (= slots)' method"""
        reference_object = validated_data.get('room') or validated_data.get('floor') or validated_data.get('table')
        # TODO: protected filter for user
        user = validated_data['user']
        if isinstance(reference_object, Room):
            tables = list(reference_object.tables)
        elif isinstance(reference_object, Floor):
            tables = list(Table.objects.filter(room__in=list(reference_object.rooms)))
        elif isinstance(reference_object, Table):
            tables = [reference_object, ]
        else:
            raise ResponseException('One of the fields ("room", "floor", "table") is required')

        if validated_data.get('tags'):
            tables = [
                table
                for table in tables
                if set(validated_data['tags']).issubset(set([tag.title for tag in table.tags.all()]))
            ]
            if not tables:
                raise ResponseException('No suitable tables found', status.HTTP_404_NOT_FOUND)

        response = []
        for slot in validated_data['slots']:
            date_from = slot.get('date_from')
            date_to = slot.get('date_to')
            slot_response = {
                "slot": {
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                },
                "available": True
            }
            for table in list(tables):
                if self.Meta.model.objects.is_overflowed(table, date_from, date_to):
                    slot_response['available'] = False
                    break
            response.append(slot_response)
        return response


class BookingActivateActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)

    # table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all())

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


class BookingListSerializer(BookingSerializer, BaseBookingSerializer):
    """Serialize booking list"""

    class Meta:
        model = Booking
        fields = '__all__'

    def to_representation(self, instance):
        instance: Booking
        response = super(BaseBookingSerializer, self).to_representation(instance)
        response['table'] = {"id": instance.table.id,
                             "title": instance.table.title,
                             "has_voted": False}
        response['room'] = {"id": instance.table.room.id,
                            "title": instance.table.room.title,
                            "type": instance.table.room.type.title
                            }
        response['floor'] = {"id": instance.table.room.floor.id,
                             "title": instance.table.room.floor.title}
        response['office'] = {"id": instance.table.room.floor.office.id,
                              "title": instance.table.room.floor.office.title}
        return response


class BookingActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)


class BookingDeactivateActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Booking
        fields = ['booking']

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance=instance).to_representation(instance=instance)
        return response

    def update(self, instance, validated_data):
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        instance.set_booking_over()
        validated_data['date_to'] = now
        return super(BookingDeactivateActionSerializer, self).update(instance, validated_data)


class BookingFastSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    theme = serializers.CharField(required=False)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all())
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'office', 'type', 'theme', 'user']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance).data
        response['room'] = {"id": instance.table.room.id,
                            "title": instance.table.room.title}
        response['floor'] = {"id": instance.table.room.floor.id,
                             "title": instance.table.room.floor.title}
        response['office'] = {"id": instance.table.room.floor.office.id,
                              "title": instance.table.room.floor.office.title}
        return response

    def create(self, validated_data, *args, **kwargs):
        date_from = validated_data['date_from']
        date_to = validated_data['date_to']
        office = validated_data.pop('office')
        tables = list(Table.objects.filter(room__floor__office_id=office.id, room__type__id=validated_data['type'].id))
        for table in tables[:]:
            if self.Meta.model.objects.is_user_overflowed(validated_data['user'],
                                                          table.room.type.unified,
                                                          validated_data['date_from'],
                                                          validated_data['date_to']):
                raise ResponseException('User already has a booking for this date.')
            if not self.Meta.model.objects.is_overflowed(table, date_from, date_to):
                continue
            else:
                tables.remove(table)
        if len(tables) != 0:
            return self.Meta.model.objects.create(
                date_to=date_to,
                date_from=date_from,
                table=tables[0],
                user=validated_data['user']
            )
        raise serializers.ValidationError('No table found for fast booking')


# Not needed in Django version
class BookingMobileSerializer(serializers.ModelSerializer):
    # It's hard to explain, but this shit is for create multiply booking on one table
    # You send some datetime intervals and then book table on this values
    slots = SlotsSerializer(many=True, required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(required=False)

    class Meta:
        model = Booking
        fields = ['slots', 'table', 'theme']

    # def to_representation(self, instance):
    #     # TODO rewrite according to create and existing in Flask
    #     response = {'result': 'OK',
    #                 'slot': self.slots,  # TODO send only choosen slot
    #                 'booking': BaseBookingSerializer(instance).data}
    #     return response

    def create(self, validated_data):
        table = validated_data.pop('table')
        response = []
        # booking_allowed_to_create = []
        # Cycle for checking overflowing on datetimes in slots and booking if not
        # Creating response for view
        for slot in validated_data['slots']:
            date_from = slot.get('date_from')
            date_to = slot.get('date_to')
            slot_response = {}
            if self.Meta.model.objects.is_overflowed(table, date_from, date_to):
                slot_response['result'] = 'error'
                slot_response['message'] = 'Date range is overflowed by existing booking'
            else:
                slot_response['result'] = 'OK'
                # TODO override method bulk_create, handle theme field,
                #  make comments for all my code, make merge of slots
                new_booking = Booking.objects.create(date_from=date_from,
                                                     date_to=date_to,
                                                     table=table,
                                                     user=validated_data['user'])
                # booking_allowed_to_create.append(new_booking)
                slot_response['booking'] = BaseBookingSerializer(new_booking).data
            slot_response['slot'] = {"date_from": date_from.isoformat(),
                                     "date_to": date_to.isoformat()}

            response.append(slot_response)
        # Booking.objects.bulk_create(booking_allowed_to_create)
        return response


# Not needed in Django version
class BookingFastMultiplySerializer(serializers.ModelSerializer):
    slots = SlotsSerializer(many=True, required=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=False)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=False)
    theme = serializers.CharField(max_length=200, required=False)
    sms_report = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = Booking
        fields = ['slots', 'room', 'floor', 'table', 'theme', 'sms_report']


class BookingListTablesSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()


class BookListTableSerializer(serializers.ModelSerializer):
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)

    class Meta:
        model = Booking
        fields = ['table', ]

    def to_representation(self, instance):
        pass


class BookingPersonalSerializer(serializers.ModelSerializer):
    is_over = serializers.IntegerField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'is_over']


class BookingSerializerForTableSlots(serializers.ModelSerializer):
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
        response = BaseBookingSerializer(instance).data
        response['active'] = response['is_active']
        del response['is_active']
        response['user'] = instance.user_id
        response['table'] = instance.table_id
        return response


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


def bookings_future(stats):
    return {
        "booking_id": str(stats.id),
        "table_id": str(stats.table_id),
        "table_title": stats.table_title,
        "office_id": str(stats.office_id),
        "office_title": stats.office_title,
        "floor_id": str(stats.floor_id),
        "floor_title": stats.floor_title,
        "user_id": str(stats.user_id),
        "first_name": stats.first_name,
        "middle_name": stats.middle_name,
        "last_name": stats.last_name,
        "date_from": str(stats.date_from),
        "date_to": str(stats.date_to),
        "date_activate_until": str(stats.date_activate_until)
    }


def most_frequent(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)


def get_duration(duration):
    hours = int(duration / 3600)
    minutes = int(duration % 3600 / 60)
    seconds = int((duration % 3600) % 60)
    return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


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
