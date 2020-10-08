import random
from rest_framework import serializers
# Local imports
from bookings.models import Booking, Table
from bookings.validator import BookingTimeValidator


class BookingSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200, default="Без темы")
    user = serializers.SerializerMethodField()

    def get_user(self, _):
        request = self.context.get('request')
        if request:
            return request.user

    class Meta:
        model = Booking
        fields = ['date_from', 'date_to', 'table', 'theme']

    def validate(self, **attrs):
        validator = BookingTimeValidator(**attrs, exc_class=serializers.ValidationError)
        validator.validate()
        return validator.is_valid()

    def create(self, validated_data, *args, **kwargs):
        model = self.Meta.model
        table = validated_data.pop('table')
        date_from = validated_data.pop('date_from')
        date_to = validated_data.pop('date_to')
        user = validated_data.pop('user')
        code_gen = random.randint(1000, 9999)
        if model.objects.is_overflowed(table, date_from, date_to):
            raise serializers.ValidationError('Table already booked for this date.')
        return model.objects.create(date_to=date_to, date_from=date_from,
                                       table=table, date_activate_until=(date_from, date_to),
                                       code=code_gen, user=user)


class BookingActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)

    # Todo Code

    class Meta:
        model = Booking
        fields = "__all__"
