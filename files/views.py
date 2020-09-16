from rest_framework.generics import ListCreateAPIView
from files.models import File
from files.serializers import FileSerializer


class ListCreateFilesView(ListCreateAPIView):
	serializer_class = FileSerializer
	queryset = File.objects.all()
	# permission_classes = [IsAdminUser]

