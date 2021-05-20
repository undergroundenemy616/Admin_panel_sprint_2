from rest_framework.generics import GenericAPIView
from rest_framework.mixins import Response, status
from rest_framework.parsers import FormParser, MultiPartParser

from core.permissions import IsAdmin
from files.models import File
from files.serializers_admin import (AdminFileCreateSerializer,
                                     AdminFileSerializer)


class AdminCreateFilesView(GenericAPIView):
    serializer_class = AdminFileCreateSerializer
    queryset = File.objects.all()
    permission_classes = [IsAdmin, ]
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.FILES)
        serializer.is_valid(raise_exception=True)
        saved_file = serializer.save()
        if isinstance(saved_file, tuple):
            return Response(saved_file)
        return Response(AdminFileSerializer(instance=saved_file).data,
                        status=status.HTTP_201_CREATED)
