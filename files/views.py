from rest_framework.generics import ListCreateAPIView
from core.permissions import IsAuthenticated
from rest_framework.mixins import Response, status

from files.models import File
from files.serializers import FileSerializer


class ListCreateFilesView(ListCreateAPIView):
    serializer_class = FileSerializer
    queryset = File.objects.all()
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.FILES)
        serializer.is_valid(raise_exception=True)
        saved_file = serializer.save()
        return Response(serializer.to_representation(instance=saved_file),
                        status=status.HTTP_201_CREATED)
