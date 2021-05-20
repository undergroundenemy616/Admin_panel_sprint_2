from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response

from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from offices.models import Office
from offices.serializers import (MobileSimpleOfficeBaseSerializer,
                                 OptimizeListOfficeSerializer,
                                 SwaggerOfficeParametrs,
                                 TestOfficeBaseSerializer)
from offices.serializers_mobile import (MobileOfficeBaseSerializer,
                                        MobileOfficeSerializer)


class MobileRetrieveOfficeView(RetrieveModelMixin,
                               GenericAPIView):
    """Detail Office view. All request required {id}"""
    serializer_class = MobileOfficeSerializer
    queryset = Office.objects.all()
    permission_classes = (IsAdmin, )

    def get(self, request, *args, **kwargs):
        """Get detail office by primary key."""
        return self.retrieve(request, *args, **kwargs)


class MobileListOfficeView(ListModelMixin,
                           GenericAPIView):
    """Office View."""
    serializer_class = MobileOfficeBaseSerializer
    queryset = Office.objects.all().prefetch_related(
        'zones', 'zones__groups', 'zones__groups__accounts', 'floors', 'images').select_related('license')
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    @swagger_auto_schema(query_serializer=SwaggerOfficeParametrs)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('id'):
            self.pagination_class = None
            try:
                office = self.queryset.get(id=request.query_params.get('id'))
            except ObjectDoesNotExist:
                return Response("Office not found", status=status.HTTP_404_NOT_FOUND)
            return Response(MobileOfficeBaseSerializer(instance=office).data, status=status.HTTP_200_OK)
        return self.list(request, *args, **kwargs)
