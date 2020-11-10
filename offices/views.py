from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from core.pagination import DefaultPagination
from core.permissions import IsAuthenticated
from offices.models import Office, OfficeZone
from offices.serializers import (
    CreateOfficeSerializer,
    NestedOfficeSerializer,
    CreateUpdateOfficeZoneSerializer,
    OfficeZoneSerializer
)
from rest_framework.generics import GenericAPIView, get_object_or_404
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
    serializer_class = NestedOfficeSerializer
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

    def post(self, request, *args, **kwargs):
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
    permission_classes = (AllowAny,)
    serializer_class = CreateUpdateOfficeZoneSerializer

    def get(self, request, *args, **kwargs):
        requested_zone = get_object_or_404(OfficeZone, pk=request.query_params.get('id'))
        return Response(OfficeZoneSerializer(instance=requested_zone).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if request.data['title'] and not isinstance(request.data['title'], list):
            request.data['title'] = [request.data['title']]
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_type = serializer.save(data=request.data)
        return Response(serializer.to_representation(created_type), status=status.HTTP_201_CREATED)


class UpdateDeleteZoneView(GenericAPIView, DestroyModelMixin):
    queryset = OfficeZone.objects.all()
    serializer_class = CreateUpdateOfficeZoneSerializer
    permission_classes = (AllowAny, )

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

    def get(self, request, pk=None, *args, **kwargs):
        office_zones = OfficeZone.objects.filter(groups=pk)
        response = []
        if len(office_zones) != 0:
            item = {}
            for zone in office_zones:
                # response.append(OfficeZoneSerializer(instance=zone).data)
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
