from rest_framework.generics import ListCreateAPIView
from rest_framework.mixins import Response, status
from rest_framework.parsers import FormParser, MultiPartParser

from core.permissions import IsAuthenticated
from files.models import File
from files.serializers_mobile import (MobileBaseFileSerializer,
                                      MobileFileSerializer)


class MobileListCreateFilesView(ListCreateAPIView):
    serializer_class = MobileFileSerializer
    queryset = File.objects.all()
    permission_classes = [IsAuthenticated, ]
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.FILES)
        serializer.is_valid(raise_exception=True)
        saved_file = serializer.save()
        if isinstance(saved_file, tuple):
            return Response(saved_file)
        return Response(MobileBaseFileSerializer(instance=saved_file).data,
                        status=status.HTTP_201_CREATED)
