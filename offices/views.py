import orjson
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin)
from rest_framework.response import Response

from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated
from offices.models import Office, OfficeZone
from offices.serializers import (CreateOfficeSerializer,
                                 CreateUpdateOfficeZoneSerializer,
                                 ListOfficeSerializer,
                                 MobileSimpleOfficeBaseSerializer,
                                 OfficeZoneSerializer,
                                 OptimizeListOfficeSerializer,
                                 SwaggerOfficeParametrs, SwaggerZonesParametrs,
                                 TestOfficeBaseSerializer)


class ListCreateUpdateOfficeView(ListModelMixin,
                                 CreateModelMixin,
                                 GenericAPIView):
    """Office View."""
    serializer_class = ListOfficeSerializer
    queryset = Office.objects.all().prefetch_related(
        'zones', 'zones__groups', 'zones__groups__accounts', 'floors', 'images').select_related('license')
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    @swagger_auto_schema(query_serializer=SwaggerOfficeParametrs)
    def get(self, request, *args, **kwargs):
        """Get list of all offices."""
        self.serializer_class = OptimizeListOfficeSerializer
        if request.query_params.get('search'):
            return self.list(request, *args, **kwargs)
        if request.query_params.get('start') and request.query_params.get('limit'):
            self.serializer_class = OptimizeListOfficeSerializer
        if request.query_params.get('id'):
            self.pagination_class = None
            try:
                office = self.queryset.get(id=request.query_params.get('id'))
            except ObjectDoesNotExist:
                return Response("Office not found", status=status.HTTP_404_NOT_FOUND)
            return Response(MobileSimpleOfficeBaseSerializer(instance=office).data, status=status.HTTP_200_OK)
        response = TestOfficeBaseSerializer(instance=self.queryset.all(), many=True).data
        response = {'results': response}
        return Response(data=response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        serializer = CreateOfficeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RetrieveUpdateDeleteOfficeView(UpdateModelMixin,
                                     RetrieveModelMixin,
                                     DestroyModelMixin,
                                     GenericAPIView):
    """Detail Office view. All request required {id}"""
    serializer_class = CreateOfficeSerializer
    queryset = Office.objects.all()
    permission_classes = (IsAdmin, )

    def get(self, request, *args, **kwargs):
        """Get detail office by primary key."""
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """Edit detail office by primary key."""
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):  # good
        """Delete office by primary key."""
        return self.destroy(request, *args, **kwargs)


class ListOfficeZoneView(GenericAPIView):
    queryset = OfficeZone.objects.all()
    serializer_class = CreateUpdateOfficeZoneSerializer
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(query_serializer=SwaggerZonesParametrs)
    def get(self, request, *args, **kwargs):
        requested_zone = get_object_or_404(OfficeZone, pk=request.query_params.get('id'))
        return Response(OfficeZoneSerializer(instance=requested_zone).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        if request.data['title'] and not isinstance(request.data['title'], list):
            request.data['title'] = [request.data['title']]
        elif isinstance(request.data['title'], list):
            request.data['group_whitelist_visit'] = []
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_type = serializer.save(data=request.data)
        return Response(serializer.to_representation(created_type), status=status.HTTP_201_CREATED)


class UpdateDeleteZoneView(GenericAPIView, DestroyModelMixin):
    queryset = OfficeZone.objects.all()
    serializer_class = CreateUpdateOfficeZoneSerializer
    permission_classes = (IsAdmin, )

    def put(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(OfficeZone, pk=pk)
        if not instance.is_deletable:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if request.data['title'] and not isinstance(request.data['title'], list):
            request.data['title'] = [request.data['title']]
            request.data['office'] = instance.office.id
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)
        created_type = serializer.save()
        return Response(serializer.to_representation(created_type), status=status.HTTP_200_OK)

    def delete(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(OfficeZone, pk=pk)
        if not instance.is_deletable:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return self.destroy(request, *args, **kwargs)


class GroupAccessView(GenericAPIView):
    queryset = OfficeZone.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = SwaggerOfficeParametrs

    def get(self, request, pk=None, *args, **kwargs):
        office_zones = OfficeZone.objects.filter(groups=pk)
        response = []
        if len(office_zones) != 0:
            item = {}
            for zone in office_zones:
                item['id'] = zone.office.id
                item['title'] = zone.office.title
                item['description'] = zone.office.description
                item['zones'] = []
                response.append(item)
            response = list({item['id']: item for item in response}.values())
            for item in response:
                filtered_zones = office_zones.filter(office=item['id'])
                for filtered_zone in filtered_zones:
                    item['zones'].append({
                        'id': str(filtered_zone.id),
                        'title': filtered_zone.title
                    })
        return Response(response, status=status.HTTP_200_OK)
