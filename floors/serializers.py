from rest_framework import serializers
from floors.models import Floor
from rooms.serializers import RoomSerializer


class FloorSerializer(serializers.ModelSerializer):
	occupied = serializers.ReadOnlyField()
	capacity = serializers.ReadOnlyField()
	occupied_tables = serializers.ReadOnlyField()
	capacity_tables = serializers.ReadOnlyField()
	occupied_meeting = serializers.ReadOnlyField()
	capacity_meeting = serializers.ReadOnlyField()
	rooms = RoomSerializer(many=True)

	class Meta:
		model = Floor
		fields = '__all__'
