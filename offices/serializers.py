from rest_framework import serializers
from offices.models import Office
from files.models import File
from licenses.models import License
from floors.serializers import FloorSerializer


class CreateOfficeSerializer(serializers.ModelSerializer):
    floors_number = serializers.IntegerField(min_value=0, required=False)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)

    class Meta:
        model = Office
        fields = '__all__'


class FilterOfficeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(max_length=256, required=False)
    tags = serializers.ListField(required=False)
    start = serializers.IntegerField(min_value=1, required=False)
    limit = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = Office
        fields = ['type', 'tags', 'start', 'limit']


class EditOfficeSerializer(serializers.ModelSerializer):
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(), required=False)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
    floors_number = serializers.IntegerField(min_value=0, required=False)

    class Meta:
        model = Office
        fields = '__all__'


class OfficeSerializer(serializers.ModelSerializer):
    occupied = serializers.ReadOnlyField()
    capacity = serializers.ReadOnlyField()
    occupied_tables = serializers.ReadOnlyField()
    capacity_tables = serializers.ReadOnlyField()
    occupied_meeting = serializers.ReadOnlyField()
    capacity_meeting = serializers.ReadOnlyField()
    floors = FloorSerializer(many=True)
    floors_number = serializers.ReadOnlyField()

    class Meta:
        model = Office
        fields = '__all__'
