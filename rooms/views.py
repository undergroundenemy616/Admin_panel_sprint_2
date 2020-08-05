from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rooms.models import Room
from rooms.serializers import RoomSerializer


class ListOffices(APIView):
	permission_classes = [IsAdminUser]
	serializer_class = RoomSerializer

