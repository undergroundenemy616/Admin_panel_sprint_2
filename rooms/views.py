from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rooms.models import Room
from rooms.serializers import RoomSerializer
from rest_framework.response import Response


class ListRooms(APIView):
	# permission_classes = [IsAdminUser]
	serializer_class = RoomSerializer

	def get(self, request, format=None):
		return Response([RoomSerializer(room).data for room in Room.objects.all()])
