from datetime import datetime

from rest_framework import serializers, status
from backends.handlers import ResponseException
from bookings.models import Booking, Table
from bookings.validator import BookingTimeValidator
from floors.models import Floor
from rooms.models import Room
import random

from users.models import User


class BookingSerializer(serializers.ModelSerializer):
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
        if self.Meta.model.objects.is_overflowed(
                validated_data['table'],
                validated_data['date_from'],
                validated_data['date_to']
        ):
            raise ResponseException('Table already booked for this date.')
        return self.Meta.model.objects.create(
            date_to=validated_data['date_to'],
            date_from=validated_data['date_from'],
            table=validated_data['table'],
            code=random.randint(1000, 9999),
            user=validated_data['user']
        )

    def to_representation(self, instance: Booking):
        # response = super(BookingSerializer, self).to_representation(instance)
        data = {
            "id": instance.id,
            "code": instance.code,
            "is_over": False if instance.date_to >= datetime.utcnow() else True,
            "active": instance.is_active,
            "date_from": instance.date_from,
            "date_to": instance.date_to,
            "date_activate_until": instance.date_activate_until,
            "table": {
                # TODO: Create TableSerializer.to_short_representation
                "id": instance.table.id,
                "title": instance.table.title
            },
            "user": {
                # TODO: Create UserSerializer.to_representation
                "id": instance.user.id
            }
        }
        # data = super(FloorMapSerializer, self).to_representation(instance)
        # data['image'] = FileSerializer(instance=instance.image).data
        # data['floor'] = BaseFloorSerializer(instance=instance.floor).data
        # return data
        pass


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


class BookingActionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=True)

    # Todo Code

    class Meta:
        model = Booking
        fields = "__all__"
