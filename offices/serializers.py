from rest_framework import serializers
from offices.models import Office
from floors.serializers import FloorSerializer


class OfficeSerializer(serializers.ModelSerializer):
	occupied = serializers.ReadOnlyField()
	capacity = serializers.ReadOnlyField()
	occupied_tables = serializers.ReadOnlyField()
	capacity_tables = serializers.ReadOnlyField()
	occupied_meeting = serializers.ReadOnlyField()
	capacity_meeting = serializers.ReadOnlyField()
	floors = FloorSerializer(many=True)

	class Meta:
		model = Office
		fields = '__all__'
