import random
from datetime import datetime, timedelta
from django.db.models import Q
from rest_framework import serializers
# Local imports
from bookings.models import Booking, Table

MINUTES_TO_ACTIVATE = 15


def date_validator(value):
    if value < datetime.utcnow():
        raise ValueError("Cannot create booking in the past")
    return value


class BookingSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True, validators=[date_validator])
    date_to = serializers.DateTimeField(validators=[date_validator])
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200, default="Без темы")

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme']

    def create(self, validated_data, *args, **kwargs):
        model = self.Meta.model
        table = validated_data.pop('table')
        date_from = validated_data.pop('date_from')
        date_to = validated_data.pop('date_to')
        code_gen = random.randint(1000, 9999)

        if date_to < date_from:
            raise serializers.ValidationError("Ending time should be larger than the starting one")

        overflows = Booking.check_overflow()

        # overflows = Booking.objects.filter(table=table, is_over=False). \
        #     filter(Q(date_from__gte=date_from, date_from__lte=date_to)
        #            | Q(date_from__lte=date_from, date_to__gte=date_to)
        #            | Q(date_from__gte=date_from, date_to__lte=date_to)
        #            | Q(date_to__gt=date_from, date_to__lt=date_to))
        if overflows:
            raise serializers.ValidationError("Table already booked")

        date_now = datetime.utcnow()
        if date_now <= date_from:
            if date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):
                date_activate_until = date_from + timedelta(minutes=MINUTES_TO_ACTIVATE)
            else:
                date_activate_until = date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
        elif date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):
            date_activate_until = date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
        else:
            date_activate_until = date_to

        booking = model.objects.create(date_to=date_to, date_from=date_from,
                                       table=table, date_activate_until=date_activate_until,
                                       code=code_gen, user=args[0])  # TODO refactor user and theme fields


class BookingActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)

    # Todo Code

    class Meta:
        model = Booking
        fields = "__all__"
