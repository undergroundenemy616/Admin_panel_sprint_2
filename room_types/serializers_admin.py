from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.serializers import TestBaseFileSerializer
from offices.models import Office
from room_types.models import RoomType


def exist_table_for_room_type(rooms):
    for room in rooms:
        if room.tables.exists():
            return True
    return False


class AdminRoomTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = RoomType
        fields = '__all__'

    def to_representation(self, instance):
        response = super(AdminRoomTypeSerializer, self).to_representation(instance)
        response['pre_defined'] = not instance.is_deletable
        response['icon'] = TestBaseFileSerializer(instance=instance.icon).data if instance.icon else None
        response['available_for_book'] = exist_table_for_room_type(instance.rooms.all()) if instance.bookable else False
        return response


class AdminRoomTypeCreateSerializer(serializers.ModelSerializer):
    titles = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = RoomType
        fields = ['titles', 'bookable', 'unified', 'work_interval_days', 'work_interval_hours', 'office']

    def validate(self, attrs):
        if RoomType.objects.filter(title__in=attrs.get('titles'), office=attrs.get('office')).exists():
            raise ValidationError(detail={"message": "RoomType already exists"}, code=400)
        return attrs

    @atomic()
    def create(self, validated_data):
        room_types_to_create = []

        for title in set(validated_data['titles']):
            room_type = RoomType(title=title, office=validated_data.get('office'))
            if validated_data.get('bookable'):
                room_type.bookable = validated_data['bookable']
            if validated_data.get('unified'):
                room_type.unified = validated_data['unified']
            if validated_data.get('work_interval_days'):
                room_type.work_interval_days = validated_data['work_interval_days']
            if validated_data.get('work_interval_hours'):
                room_type.work_interval_hours = validated_data['work_interval_hours']
            room_types_to_create.append(room_type)

        office_zones = RoomType.objects.bulk_create(room_types_to_create)
        return office_zones

    def to_representation(self, instance):
        response = dict()
        if isinstance(instance, RoomType):
            response['result'] = AdminRoomTypeSerializer(instance=instance).data
        else:
            response['result'] = AdminRoomTypeSerializer(instance=instance, many=True).data
        return response

