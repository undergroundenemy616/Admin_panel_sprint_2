from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from offices.models import Office
from offices.serializers import OfficeSerializer
from rest_framework.response import Response


class ListOffices(APIView):
	# permission_classes = [IsAdminUser]
	serializer_class = OfficeSerializer

	def get(self, request, format=None):
		return Response([OfficeSerializer(office).data for office in Office.objects.all()])
