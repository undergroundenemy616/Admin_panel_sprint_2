from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from offices.models import Office
from offices.serializers import OfficeSerializer


class ListOffices(APIView):
	permission_classes = [IsAdminUser]
	serializer_class = OfficeSerializer
	#
	# def get(self, request, format=None):
	# 	offices = Office.objects.all()
	# 	for office in offices:

