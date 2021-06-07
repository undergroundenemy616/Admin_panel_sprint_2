from django.db.transaction import atomic
from django.shortcuts import get_list_or_404
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from core.handlers import ResponseException
from files.models import File
from files.serializers import TestBaseFileSerializer
from files.serializers_admin import AdminFileSerializer
from offices.models import Office
from rooms.models import Room
from tables.models import Table, TableMarker, TableTag


# Other Functions
def check_table_tags_exists(tags):
    """Check is every tag in array exists."""
    if not tags:
        return True

    for elem in tags:
        result = TableTag.objects.filter(id=elem.id).exists()
        if not result:
            raise ValidationError(f'Table_tag {elem} does not exists.')


# Swagger serializers
class AdminSwaggerTableTagParametrs(serializers.Serializer):
    office = serializers.UUIDField()


# Class based serializers
class AdminTableSerializer(serializers.ModelSerializer):

    class Meta:
        model = Table
        fields = ['id', 'title', 'description', 'is_occupied']

    def to_representation(self, instance):
        response = super(AdminTableSerializer, self).to_representation(instance)
        response['room'] = instance.room.id
        response['room_title'] = instance.room.title
        response['floor_title'] = instance.room.floor.title
        response['images'] = TestBaseFileSerializer(instance=instance.images, many=True).data
        response['rating'] = 0
        response['ratings'] = 0  # TODO: Looks like this is doesn't need
        response['marker'] = AdminTableMarkerSerializer(instance=instance.table_marker).data if hasattr(instance, 'table_marker') \
            else None
        response['tags'] = AdminTableTagSerializer(instance.tags.all(), many=True).data
        return response


class AdminTableCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'

    @atomic()
    def update(self, instance, validated_data):
        if validated_data.get('room') and validated_data['room'] != instance.room:
            instance.table_marker.delete()
            instance.refresh_from_db()
        return super(AdminTableCreateUpdateSerializer, self).update(instance, validated_data)

    def to_representation(self, instance):
        return AdminTableSerializer(instance=instance).data


class AdminTableMarkerSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), source='table.room', required=False)

    class Meta:
        model = TableMarker
        fields = '__all__'


class AdminTableListDeleteSerializer(serializers.Serializer):
    tables = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Table.objects.all()))

    def delete(self):
        query = get_list_or_404(Table, id__in=self.data['tables'])
        for table in query:
            table.delete()


class AdminTableTagSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)
    icon = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, allow_null=True)

    class Meta:
        model = TableTag
        fields = '__all__'

    def to_representation(self, instance):
        response = super(AdminTableTagSerializer, self).to_representation(instance)
        response['icon'] = AdminFileSerializer(instance=instance.icon).data if instance.icon else None
        return response


class AdminTableTagCreateSerializer(serializers.ModelSerializer):
    titles = serializers.ListField(child=serializers.CharField(), required=True)
    icon = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)

    class Meta:
        model = TableTag
        fields = ['id', 'titles', 'office', 'icon']

    def to_representation(self, instance):
        response = dict()
        response['results'] = AdminTableTagSerializer(instance=instance, many=True).data
        return response

    def validate(self, attrs):
        if not self.instance:
            if TableTag.objects.filter(office=attrs.get('office'), title__in=attrs.get('titles')).exists():
                raise ResponseException(detail="TableTag already exists", status_code=status.HTTP_400_BAD_REQUEST)
        return attrs

    @atomic()
    def create(self, validated_data):
        tags_to_create = []
        for tag_title in set(validated_data.get('titles')):
            tags_to_create.append(TableTag(title=tag_title, office=validated_data.get('office'),
                                           icon=validated_data.get('icon')))
        tags = TableTag.objects.bulk_create(tags_to_create)
        return tags
