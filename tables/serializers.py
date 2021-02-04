from core.handlers import ResponseException
from datetime import datetime
from typing import Any, Dict
import pytz
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import status

from files.models import File
from files.serializers import (BaseFileSerializer, FileSerializer,
                               image_serializer)
from offices.models import Office
from rooms.models import Room
from tables.models import Table, TableTag
from bookings.models import Booking
from bookings.serializers import BookingSerializer
from tables.models import Table, TableTag, TableMarker


class SwaggerTableParameters(serializers.Serializer):
    free = serializers.IntegerField(required=False)
    office = serializers.UUIDField(required=False)
    floor = serializers.UUIDField(required=False)
    room = serializers.UUIDField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class SwaggerTableSlotsParametrs(serializers.Serializer):
    date = serializers.DateField(required=False, format="%Y-%m-%d", input_formats=['%Y-%m-%d', 'iso-8601'])
    daily = serializers.IntegerField(required=False)
    monthly = serializers.IntegerField(required=False)


class SwaggerTableTagParametrs(serializers.Serializer):
    office = serializers.UUIDField()


def check_table_tags_exists(tags):
    """Check is every tag in array exists."""
    if not tags:
        return True

    for elem in tags:
        result = TableTag.objects.filter(id=elem.id).exists()
        if not result:
            raise ValidationError(f'Table_tag {elem} does not exists.')


def basic_table_serializer(table: Table) -> Dict[str, Any]:
    return {
        'id': str(table.id),
        'title': table.title,
        'description': table.description,
        'room': str(table.room.id),
        'tags': [table_tag_serializer(tag=tag) for tag in table.tags.all()],
        'images': [image_serializer(image=image) for image in table.images.all()],
        'is_occupied': table.is_occupied,
        'marker': table_marker_serializer(marker=table.table_marker).copy() if hasattr(table, 'table_marker') else None,
        'rating': table.rating
    }


def table_tag_serializer(tag: TableTag) -> Dict[str, Any]:
    return {
        'id': str(tag.id),
        'title': tag.title,
        'office': str(tag.office.id),
        'icon': image_serializer(image=tag.icon).copy() if tag.icon else None
    }


def table_marker_serializer(marker: TableMarker) -> Dict[str, Any]:
    return {
        'x': float(marker.x),
        'y': float(marker.y),
    }


class BaseTableTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = TableTag
        fields = '__all__'
        depth = 1


class TableTagSerializer(serializers.ModelSerializer):
    title = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = TableTag
        fields = '__all__'

    def to_representation(self, instance):
        if isinstance(instance, list):
            response = []
            for table_tag in instance:
                response.append(BaseTableTagSerializer(table_tag).data)
            return response
        else:
            response = BaseTableTagSerializer(instance=instance).data
            if instance.icon:
                response['icon'] = FileSerializer(instance=instance.icon).data
            response = [response]
            return response

    def create(self, validated_data):
        if len(validated_data['title']) > 1:
            titles = validated_data['title']
            table_tags_to_create = []
            for title in titles:
                if self.Meta.model.objects.filter(office_id=validated_data['office'],
                                                  title=title).exists():
                    raise ValidationError('Tag already exists')
                table_tags_to_create.append(TableTag(office=validated_data['office'], title=title))
            instance = TableTag.objects.bulk_create(table_tags_to_create)
            return instance
        else:
            validated_data['title'] = validated_data['title'][0]
            if self.Meta.model.objects.filter(office_id=validated_data['office'],
                                              title=validated_data['title']).exists():
                raise ValidationError('Tag already exists')
            return super(TableTagSerializer, self).create(validated_data)


class ListTableTagSerializer(TableTagSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)

    def to_representation(self, instance):
        return super(TableTagSerializer, self).to_representation(instance)


class UpdateTableTagSerializer(TableTagSerializer):
    title = serializers.CharField(required=False)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=False)
    icon = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, allow_null=True)

    class Meta:
        model = TableTag
        fields = ['title', 'office', 'icon']


class TableSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=TableTag.objects.all(), required=False, many=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, many=True)
    rating = serializers.ReadOnlyField()

    class Meta:
        model = Table
        fields = '__all__'
        lookup_field = 'title'
        depth = 1

    def to_representation(self, instance):
        response = super(TableSerializer, self).to_representation(instance)
        response['tags'] = BaseTableTagSerializer(instance.tags.all(), many=True).data
        response['images'] = BaseFileSerializer(instance.images.all(), many=True).data
        response['marker'] = TableMarkerSerializer(instance=instance.table_marker).data if \
            hasattr(instance, 'table_marker') else None
        return response


class CreateTableSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=True)
    tags = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=TableTag.objects.all()),
                                 validators=[check_table_tags_exists], write_only=True,
                                 allow_empty=True, required=False, allow_null=True)
    images = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=File.objects.all()),
                                   write_only=True, allow_empty=True, required=False)

    class Meta:
        model = Table
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        instance: Table
        response = super(CreateTableSerializer, self).to_representation(instance)
        response['images'] = FileSerializer(instance=instance.images, many=True).data
        response['tags'] = TableTagSerializer(instance=instance.tags, many=True).data
        response['marker'] = None
        return response

    def create(self, validated_data):
        model = self.Meta.model
        tags = validated_data.pop('tags', None)
        room = validated_data.pop('room')
        images = validated_data.pop('images')
        instance = model.objects.create(room=room, **validated_data)
        office_id = instance.room.floor.office.id
        if images:
            for image in images:
                instance.images.add(image)
        if tags:
            instance.tags.set(tags)
        return instance


class UpdateTableSerializer(CreateTableSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    title = serializers.CharField(required=False)
    tags = serializers.ListField(child=serializers.CharField(required=False),
                                 validators=[check_table_tags_exists], write_only=True,
                                 allow_empty=True, allow_null=True, required=False)
    images = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=File.objects.all()),
                                   write_only=True, allow_empty=True, required=False)

    class Meta:
        model = Table
        fields = ['room', 'description', 'title', 'tags', 'images']
        depth = 1

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        office_id = instance.room.floor.office.id
        if tags:
            tags_queryset = TableTag.objects.filter(title__in=tags, office_id=office_id)
            instance.tags.set(tags_queryset)
        return super(UpdateTableSerializer, self).update(instance, validated_data)


class TableMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableMarker
        fields = ['x', 'y', 'table']


class TableSlotsSerializer(serializers.ModelSerializer):
    date = serializers.DateField(required=False, format="%Y-%m-%d", input_formats=['%Y-%m-%d', 'iso-8601'])
    daily = serializers.IntegerField(required=False)
    monthly = serializers.IntegerField(required=False)

    class Meta:
        model = Booking
        fields = ['date', 'daily', 'monthly']
