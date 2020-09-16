from rest_framework import serializers
from rooms.models import Room
from tables.models import Table, TableTag


class TableSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=256, required=True)
    description = serializers.CharField(max_length=256, required=False)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), required=True)
    tags = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    current_rating = serializers.ReadOnlyField()

    class Meta:
        model = Table
        fields = '__all__'
        depth = 1

    def create(self, validated_data):
        model = self.Meta.model
        tags = validated_data.pop('tags', None)
        room = validated_data.pop('room')
        instance = model.objects.create(room=room, **validated_data)
        office_id = instance.room.floor.office.id
        tags_queryset = TableTag.objects.filter(title__in=tags, office_id=office_id)
        instance.tags.add(tags_queryset)
        return instance
