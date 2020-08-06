from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from tables.models import Table
from rest_framework.response import Response
from tables.serializers import TableSerializer


class ListTables(APIView):
	# permission_classes = [IsAdminUser]
	serializer_class = TableSerializer

	def get(self, request, format=None):
		return Response([TableSerializer(table).data for table in Table.objects.all()])
