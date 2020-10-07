from datetime import datetime
from rest_framework import serializers
# Local imports
from bookings.models import Booking, Table


def date_validator(value):
    if value < datetime.utcnow():
        raise ValueError("Cannot create booking in the past")
    return value


class BookingSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True, validators=[date_validator])
    date_to = serializers.DateTimeField(validators=[date_validator])
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200)

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme']

    def create(self, validated_data):
        model = self.Meta.model
        table = validated_data.pop('table')


class BookingForActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)
    # Todo Code

    class Meta:
        model = Booking
        fields = "__all__"
