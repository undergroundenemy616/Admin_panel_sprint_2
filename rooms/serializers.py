from rest_framework import serializers
from rooms.models import Room
from tables.serializers import TableSerializer


class RoomSerializer(serializers.ModelSerializer):
	occupied = serializers.ReadOnlyField()
	capacity = serializers.ReadOnlyField()
	occupied_tables = serializers.ReadOnlyField()
	capacity_tables = serializers.ReadOnlyField()
	occupied_meeting = serializers.ReadOnlyField()
	capacity_meeting = serializers.ReadOnlyField()
	tables = TableSerializer(many=True)

	class Meta:
		model = Room
		fields = '__all__'
