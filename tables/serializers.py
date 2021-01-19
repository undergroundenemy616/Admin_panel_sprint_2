from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from files.models import File
from files.serializers import FileSerializer, BaseFileSerializer
from offices.models import Office
from rooms.models import Room
from tables.models import Table, TableTag


class SwaggerTableParameters(serializers.Serializer):
    free = serializers.IntegerField(required=False)
    office = serializers.UUIDField(required=False)
    floor = serializers.UUIDField(required=False)
    room = serializers.UUIDField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class SwaggerTableTagParametrs(serializers.Serializer):
    office = serializers.UUIDField()


def check_table_tags_exists(tags):
    """Check is every tag in array exists."""
    if not tags:
        return True

    for elem in tags:
        result = TableTag.objects.filter(title=elem).exists()
        if not result:
            raise ValidationError(f'Table_tag {elem} does not exists.')


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
        response['tags'] = [BaseTableTagSerializer(instance=tag).data for tag in instance.tags.all()]
        response['images'] = [BaseFileSerializer(instance=image).data for image in instance.images.all()]
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
            tags_queryset = TableTag.objects.filter(title__in=tags, office_id=office_id)
            instance.tags.set(tags_queryset)
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
