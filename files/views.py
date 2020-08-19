from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from files.models import File
from files.serializers import FileSerializer


class ListFiles(APIView):
	# permission_classes = [IsAdminUser]
	serializer_class = FileSerializer

