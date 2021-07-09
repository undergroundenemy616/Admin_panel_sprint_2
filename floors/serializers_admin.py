from django.db.transaction import atomic
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from core.handlers import ResponseException
from files.models import File
from floors.models import Floor, FloorMap
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
        fields = '__all__'


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

    def validate(self, attrs):
        if not self.instance:
            if Floor.objects.filter(office=attrs.get('office'), title__in=attrs.get('titles')).exists():
                raise ResponseException(detail="Floor already exists", status_code=status.HTTP_400_BAD_REQUEST)
        return attrs

    @atomic()
    def create(self, validated_data):
        floors_to_create = []
        for floor_title in set(validated_data.get('titles')):
            floors_to_create.append(Floor(title=floor_title, office=validated_data.get('office')))
        floors = Floor.objects.bulk_create(floors_to_create)
        return floors


class AdminFloorMapSerializer(serializers.ModelSerializer):
    image = FloorMapImageSerializer()

    class Meta:
        model = FloorMap
        exclude = ['floor']

    def to_representation(self, instance):
        response = super(AdminFloorMapSerializer, self).to_representation(instance)
        if instance.floor:
            response['floor_id'] = instance.floor.id
            response['floor_title'] = instance.floor.title
        else:
            response['floor_id'] = None
            response['floor_title'] = None
        return response


class AdminCreateUpdateFloorMapSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())

    class Meta:
        model = FloorMap
        fields = '__all__'

    def validate(self, attrs):
        if self.instance and self.instance.floor != attrs['floor'] and attrs['floor'].floormap:
            raise ValidationError(detail="FloorMap for this floor already exists")
        elif not self.instance and hasattr(attrs['floor'], 'floormap'):
            raise ValidationError(detail="FloorMap for this floor already exists")
        return attrs

    def to_representation(self, instance):
        return AdminFloorMapSerializer(instance=instance).data


class AdminFloorClearValidation(serializers.Serializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())


