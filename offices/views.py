from django.forms import model_to_dict
from rest_framework import status
from rest_framework.response import Response
from backends.pagination import DefaultPagination
from floors.models import Floor
from groups.models import Group
from licenses.serializers import LicenseSerializer
from offices.models import Office, OfficeZone
from offices.serializers import OfficeSerializer, OfficeZoneSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (
    UpdateModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    ListModelMixin
)


class ListCreateUpdateOfficeView(ListModelMixin,
                                 CreateModelMixin,
                                 GenericAPIView):
    """Office View."""
    serializer_class = OfficeSerializer
    queryset = Office.objects.all()
    pagination_class = DefaultPagination

    # permission_classes = (IsAdminUser,)

    # def get_queryset(self):  # there are no need.
    #     queryset = self.queryset
    #     if isinstance(queryset, QuerySet):
    #         queryset = queryset.all()
    #     queryset = queryset.select_related('licenses')
    #     queryset = queryset.prefetch_related('images')
    #     queryset = queryset.prefetch_related('floors__rooms__tables')
    #     return queryset

    # def get_mapped_query(self, request):  # there are no need
    #     """Returns mapped literals for search in database."""
    #     query_params = request.query_params
    #     mapped = {"floors__rooms__type": query_params.get('type'),
    #               "floors__rooms__tables__tags__title__in": query_params.getlist('tags')}
    #
    #     items = []
    #     for field in mapped.keys():
    #         if not mapped[field]:
    #             items.append(field)
    #     for item in items:
    #         del mapped[item]
    #     return mapped

    def get(self, request, *args, **kwargs):
        """Get list of all offices."""
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):  # done, test, todo signals
        """Create office."""
        serializer: OfficeSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        office = serializer.save()
        floor = Floor.objects.create(office=office, title='Default floor.')  # create floor
        office_zone = OfficeZone.objects.create(office=office, is_deletable=False)  # create zone
        groups = Group.objects.filter(is_deletable=False)
        if groups:
            office_zone.group_whitelist.add(*groups)  # add to group whitelist
        zones_with_groups = OfficeZoneSerializer(instance=office_zone).data

        headers = self.get_success_headers(serializer.data)

        data = dict()
        data.update(serializer.data)
        data['id'] = office.id
        data['images'] = [r.id for r in serializer.validated_data.get('images', [])]
        data['license'] = LicenseSerializer(instance=serializer.validated_data['license']).data
        data['floors'] = [model_to_dict(floor)]  # todo change to serializer
        data['zones'] = zones_with_groups
        data['floors_number'] = 1
        data['occupied'] = 0
        data['capacity'] = 0
        data['occupied_tables'] = 0
        data['capacity_tables'] = 0
        data['occupied_meeting'] = 0
        data['capacity_meeting'] = 0

        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class RetrieveUpdateDeleteOfficeView(UpdateModelMixin,
                                     RetrieveModelMixin,
                                     DestroyModelMixin,
                                     GenericAPIView):
    """Detail Office view. All request required {id}"""
    serializer_class = OfficeSerializer
    queryset = Office.objects.all()

    def get(self, request, *args, **kwargs):
        """Get detail office by primary key."""
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """Edit detail office by primary key."""
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):  # good
        """Delete office by primary key."""
        return self.destroy(request, *args, **kwargs)
