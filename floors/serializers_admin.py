from django.db.transaction import atomic
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from files.models import File
from floors.models import Floor, FloorMap
from floors.serializers import FloorMapSerializer
from offices.models import Office
from room_types.models import RoomType


def room_type_title_validator(value):
    if not RoomType.objects.filter(title=value).exists():
        raise ValidationError(detail='Invalid room_type title', code=400)


class AdminFloorForOfficeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Floor
        fields = ['id', 'title']


class FloorMapImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'title', 'path', 'thumb']


class FloorMapSetSerializer(serializers.ModelSerializer):
    image = FloorMapImageSerializer(read_only=True)

    class Meta:
        model = FloorMap
        fields = ['id', 'width', 'height', 'image']


class AdminSingleFloorSerializer(serializers.ModelSerializer):
    floor_map = FloorMapSetSerializer(read_only=True, source='floormap', required=False, allow_null=True)

    class Meta:
        model = Floor
        fields = ['id', 'title', 'description', 'office', 'floor_map']

    def to_representation(self, instance):
        response = super(AdminSingleFloorSerializer, self).to_representation(instance)
        return response


class AdminFloorSerializer(serializers.ModelSerializer):
    floor_map = FloorMapSetSerializer(read_only=True, source='floormap', required=False, allow_null=True)
    titles = serializers.ListField(child=serializers.CharField(), required=True)

    class Meta:
        model = Floor
        fields = ['id', 'titles', 'description', 'office', 'floor_map']

    def to_representation(self, instance):
        response = dict()
        response['results'] = AdminSingleFloorSerializer(instance=instance, many=True).data
        return response

    @atomic()
    def create(self, validated_data):
        floors_to_create = []
        for floor_title in validated_data.get('titles'):
            floors_to_create.append(Floor(title=floor_title, office=validated_data.get('office')))
        floors = Floor.objects.bulk_create(floors_to_create)
        return floors


class AdminFloorMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorMap
        fields = '__all__'

