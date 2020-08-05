from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from tables.models import Table
from tables.serializers import TableSerializer


class ListTables(APIView):
	permission_classes = [IsAdminUser]
	serializer_class = TableSerializer

