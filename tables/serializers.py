from rest_framework import serializers
from tables.models import Table


class TableSerializer(serializers.ModelSerializer):
    current_rating = serializers.ReadOnlyField()

    class Meta:
        model = Table
        fields = '__all__'
        depth = 1


class CreateTableSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=256, required=True)
    description = serializers.CharField(max_length=256, required=False)
    room = serializers.CharField(required=True)
    tags = serializers.ListField(required=False)

    class Meta:
        model = Table
        fields = ['room', 'title', 'description', 'tags']
