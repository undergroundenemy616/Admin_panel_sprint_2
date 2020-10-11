import random
from rest_framework import serializers
from bookings.models import Booking, Table
from bookings.validator import BookingTimeValidator
from floors.models import Floor
from rooms.models import Room
from tables.models import TableTag
from users.models import User


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

    def create(self, validated_data, *args, **kwargs):
        table = validated_data.pop('table')
        date_from = validated_data.pop('date_from')
        date_to = validated_data.pop('date_to')
        code_gen = random.randint(1000, 9999)
        if self.Meta.model.objects.is_overflowed(table, date_from, date_to):
            raise serializers.ValidationError('Table already booked for this date.')
        return self.Meta.model.objects.create(
            date_to=date_to,
            date_from=date_from,
            table=table,
            code=code_gen,
            user=validated_data['user']
        )


class SlotsSerializer(serializers.Serializer):
    """Serialize and validate multiple booking time periods"""
    date_from = serializers.DateTimeField(required=True)
    date_to = serializers.DateTimeField(required=True)

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
        reference_object = validated_data.get('room') \
            or validated_data.get('floor') \
            or validated_data.get('table')

        # TODO: protected filter for user
        user = validated_data['user']
        if isinstance(reference_object, Room):
            tables = reference_object.tables.all()
        elif isinstance(reference_object, Floor):
            tables = Table.objects.filter(room__in=list(reference_object.rooms.all()))
        elif isinstance(reference_object, Table):
            tables = [reference_object, ]
        else:
            raise serializers.ValidationError('One of the fields ("room", "floor", "table") is required')

        # if validated_data.get('tags'):
            # TODO: Refactor
            # tables = Table.objects.filter(id__in=[str(table.id) for table in tables]).filter(
            #     tags__in=list(
            #         TableTag.objects.filter(title__in=validated_data['tags'])
            #     )
            # )
            # tables = tables.filter(tags__in=list(TableTag.objects.filter(title__in=validated_data['tags'])))
            # if not tables:
            #     return {"message": "No suitable tables found"}, 400

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
