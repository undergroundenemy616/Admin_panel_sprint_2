from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from files.models import File
from files.serializers import FileSerializer
from offices.models import Office
from rooms.models import Room
from tables.models import Table, TableTag


def check_table_tags_exists(tags):
    """Check is every tag in array exists."""
    if not tags:
        return True

    for elem in tags:
        result = TableTag.objects.filter(title=elem).exists()
        if not result:
            raise ValidationError(f'Table_tag {elem} does not exists.')


class TableTagSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)
    icon = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False)

    class Meta:
        model = TableTag
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.icon:
            response['icon'] = FileSerializer(instance=instance.icon).data
        return response


class TableSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=TableTag.objects.all(), required=False, many=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, many=True)
    current_rating = serializers.ReadOnlyField()

    class Meta:
        model = Table
        fields = '__all__'
        lookup_field = 'title'
        depth = 1


class CreateTableSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=True)
    tags = serializers.ListField(child=serializers.CharField(), validators=[check_table_tags_exists], write_only=True,
                                 allow_empty=True, required=False)
    images = serializers.ListField(child=serializers.CharField(), write_only=True, allow_empty=True, required=False)

    class Meta:
        model = Table
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        instance: Table
        response = super(CreateTableSerializer, self).to_representation(instance)
        response['images'] = FileSerializer(instance=instance.images, many=True).data
        response['tags'] = TableTagSerializer(instance=instance.tags, many=True).data
        response['current_rating'] = 0
        return response

    def create(self, validated_data):
        model = self.Meta.model
        tags = validated_data.pop('tags', None)
        room = validated_data.pop('room')
        instance = model.objects.create(room=room, **validated_data)
        office_id = instance.room.floor.office.id
        if tags:
            tags_queryset = TableTag.objects.filter(title__in=tags, office_id=office_id)
            instance.tags.set(tags_queryset)
        return instance


class UpdateTableSerializer(CreateTableSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=False)
    description = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), validators=[check_table_tags_exists], write_only=True,
                                 allow_empty=True, allow_null=True, required=False)
    images = serializers.ListField(child=serializers.CharField(), write_only=True, allow_empty=True, required=False)

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
