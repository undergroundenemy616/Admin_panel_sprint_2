from datetime import datetime, timezone
from rest_framework import serializers, status
from backends.handlers import ResponseException
from bookings.models import Booking, Table
from bookings.validators import BookingTimeValidator
from floors.models import Floor
from offices.models import Office
from room_types.models import RoomType
from rooms.models import Room
from users.models import User


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

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance).data
        response['room'] = instance.table.room.id  # TODO add repr like in Flask(id, title)
        response['floor'] = instance.table.room.floor.id  # TODO add repr like in Flask(id, title)
        return response

    def create(self, validated_data, *args, **kwargs):
        if self.Meta.model.objects.is_overflowed(validated_data['table'],
                                                 validated_data['date_from'],
                                                 validated_data['date_to']):
            raise ResponseException('Table already booked for this date.')
        # TODO make theme handled
        return self.Meta.model.objects.create(
            date_to=validated_data['date_to'],
            date_from=validated_data['date_from'],
            table=validated_data['table'],
            user=validated_data['user']
        )


class BookingAdminSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200, default="Без темы")
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme', 'user']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def create(self, validated_data, *args, **kwargs):
        return BookingSerializer.create(validated_data, *args, **kwargs)


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
    # booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all())

    class Meta:
        model = Booking
        fields = ["table"]

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance).data
        return response

    def update(self, instance, validated_data):
        if validated_data['user'] != instance.user:
            raise serializers.ValidationError('Access denied')
        if validated_data['table'] != instance.table:
            raise serializers.ValidationError('Wrong data')
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        if not date_now < instance.date_activate_until:
            raise serializers.ValidationError('Activation time have passed')
        validated_data['is_active'] = True
        return super(BookingActivateActionSerializer, self).update(instance, validated_data)


class BookingDeactivateActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Booking
        fields = ['booking']

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance).data
        return response

    def update(self, instance, validated_data):
        validated_data['is_over'] = True
        validated_data['date_to'] = datetime.utcnow().replace(tzinfo=timezone.utc)
        return super(BookingDeactivateActionSerializer, self).update(instance, validated_data)


class BookingFastSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    theme = serializers.CharField(required=False)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all())
    room_type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'office', 'room_type', 'theme']

    def validate(self, attrs):
        return BookingTimeValidator(**attrs, exc_class=serializers.ValidationError).validate()

    def to_representation(self, instance):
        response = BaseBookingSerializer(instance).data
        response['room'] = instance.table.room.id
        response['floor'] = instance.table.room.floor.id
        return response

    def create(self, validated_data, *args, **kwargs):
        date_from = validated_data['date_from']
        date_to = validated_data['date_to']
        office = validated_data.pop('office')
        tables = list(Table.objects.filter(room__floor__office_id=office, room___id=validated_data['room_type']))
        for table in tables[:]:
            if not self.Meta.model.objects.is_overflowed(table, date_from, date_to):
                continue
            else:
                tables.remove(table)
        return self.Meta.model.objects.save_or_merge(
            date_to=date_to,
            date_from=date_from,
            table=tables[0],
            user=validated_data['user']
        )


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


class BookingFastMultiplySerializer(serializers.ModelSerializer):
    slots = SlotsSerializer(many=True, required=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=False)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), required=False)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=False)
    theme = serializers.CharField(max_length=200, required=False)
    # tags =
    sms_report = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = Booking
        fields = ['slots', 'room', 'floor', 'table', 'theme', 'tags', 'sms_report']
