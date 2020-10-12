import random
from datetime import datetime
from rest_framework import serializers
# Local imports
from bookings.models import Booking, Table
from bookings.validators import BookingTimeValidator


class BookingSerializer(serializers.ModelSerializer):
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    theme = serializers.CharField(max_length=200, default="Без темы")

    class Meta:
        model = Booking
        fields = '__all__'

    def validate(self, **attrs):
        validator = BookingTimeValidator(**attrs, exc_class=serializers.ValidationError)
        validator.validate()
        return validator.is_valid()

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['room'] = instance.table.room
        response['floor'] = instance.table.room.floor
        return response

    def create(self, validated_data, *args, **kwargs):
        model = self.Meta.model
        table = validated_data.pop('table')
        date_from = validated_data.pop('date_from')
        date_to = validated_data.pop('date_to')
        user = validated_data.pop('user')
        if model.objects.is_overflowed(table, date_from, date_to):
            raise serializers.ValidationError('Table already booked for this date.')
        if not table.room.type.unified:
            return model.objects.create(date_to=date_to, date_from=date_from,
                                        table=table, date_activate_until=(date_from, date_to),
                                        user=user)
        return model.objects.create(date_to=date_to, date_from=date_from,
                                    table=table, date_activate_until=(date_from, date_to),
                                    user=user, theme=validated_data('theme'))


class BookingActivateActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all())

    class Meta:
        model = Booking
        fields = "__all__"

    def update(self, instance, validated_data):
        user = validated_data.pop('user')
        if user != instance.user:
            raise serializers.ValidationError('Access denied')
        table = validated_data.pop('table')
        if table != instance.table:
            raise serializers.ValidationError('Wrong data')
        date_now = datetime.utcnow()
        if not date_now > instance.date_activate_until:
            raise serializers.ValidationError('Activation time have passed')
        instance.update(is_active=True)
        return instance


class BookingDeactivateActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.update(is_over=True, date_to=datetime.utcnow())
        return instance
