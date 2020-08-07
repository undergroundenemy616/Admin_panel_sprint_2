from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from floors.models import Floor
from floors.serializers import FloorSerializer
from rest_framework.response import Response


class ListFloors(APIView):
	# permission_classes = [IsAdminUser]
	serializer_class = FloorSerializer

	def get(self, request, format=None):
		return Response([FloorSerializer(room).data for room in Floor.objects.all()])

