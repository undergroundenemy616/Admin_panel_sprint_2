from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from floors.models import Floor
from floors.serializers import FloorSerializer


class ListFloors(APIView):
	permission_classes = [IsAdminUser]
	serializer_class = FloorSerializer

