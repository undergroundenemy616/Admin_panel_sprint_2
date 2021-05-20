from rest_framework import serializers

from bookings.models import Booking
from files.serializers_mobile import MobileBaseFileSerializer
from tables.models import Table, TableTag


class MobileTableSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()


class MobileBaseTableTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = TableTag
        fields = '__all__'
        depth = 1


class MobileTableTagSerializer(serializers.ModelSerializer):
    title = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = TableTag
        fields = '__all__'

    def to_representation(self, instance):
        if isinstance(instance, list):
            response = []
            for table_tag in instance:
                response.append(MobileBaseTableTagSerializer(table_tag).data)
            return response
        else:
            response = MobileBaseTableTagSerializer(instance=instance).data
            if instance.icon:
                response['icon'] = MobileBaseFileSerializer(instance=instance.icon).data
            response = [response]
            return response


class MobileShortTableTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableTag
        fields = ['id', 'title']


class MobileTableSlotsSerializer(serializers.ModelSerializer):
    date = serializers.DateField(required=False, format="%Y-%m-%d",
                                 input_formats=['%Y-%m-%d', 'iso-8601'])
    daily = serializers.IntegerField(required=False)
    monthly = serializers.IntegerField(required=False)

    class Meta:
        model = Booking
        fields = ['date', 'daily', 'monthly']


class MobileDetailedTableSerializer(serializers.ModelSerializer):
    images = MobileBaseFileSerializer(required=False, many=True, allow_null=True)
    tags = MobileShortTableTagSerializer(required=False, many=True, allow_null=True)

    class Meta:
        model = Table
        fields = ['id', 'title', 'description',
                  'is_occupied', 'images', 'tags']

    def to_representation(self, instance):
        response = super(MobileDetailedTableSerializer, self).to_representation(instance)
        response['office'] = {
            'id': instance.room.floor.office.id,
            'title': instance.room.floor.office.title
        }
        response['floor'] = {
            'id': instance.room.floor.id,
            'title': instance.room.floor.title
        }
        response['room'] = {
            'id': instance.room.id,
            'title': instance.room.title,
            'type': instance.room.type.title if instance.room.type else None,
            'images': MobileBaseFileSerializer(instance=instance.room.images, many=True).data
        }
        response['is_bookable'] = True  # Because Oleg, don`t be mad :^(
        return response
