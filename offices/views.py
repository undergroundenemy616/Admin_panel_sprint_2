from django.db.models import QuerySet
from backends.pagination import DefaultPagination
from offices.models import Office
from offices.serializers import OfficeSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin, CreateModelMixin, ListModelMixin
from rest_framework.response import Response


def get_mapped_query(request):
    """Returns mapped literals for search in database."""
    query_params = request.query_params
    mapped = {"floors__rooms__type": query_params.get('type'),
              "floors__rooms__tables__tags__title__in": query_params.getlist('tags')}

    items = []
    for field in mapped.keys():
        if not mapped[field]:
            items.append(field)
    for item in items:
        del mapped[item]
    return mapped


class ListCreateUpdateOfficeView(ListModelMixin,
                                 CreateModelMixin,
                                 UpdateModelMixin,
                                 GenericAPIView):
    serializer_class = OfficeSerializer
    queryset = Office.objects.all()
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser,)

    def get_queryset(self):
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        queryset = queryset.select_related('licenses')
        queryset = queryset.prefetch_related('images')
        queryset = queryset.prefetch_related('floors__rooms__tables')

        return queryset

    def list(self, request, *args, **kwargs):
        mapped = get_mapped_query(request)
        queryset = self.get_queryset()
        if mapped:
            queryset = self.queryset.filter(**mapped)

        queryset = self.filter_queryset(queryset)  # django filtering
        page = self.paginate_queryset(queryset)  # rest page pagination
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)  # rest response by pagination
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
