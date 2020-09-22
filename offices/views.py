from django.db.models import QuerySet
from backends.mixins import FilterListMixin
from backends.pagination import DefaultPagination
from offices.models import Office
from offices.serializers import OfficeSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin, CreateModelMixin


class ListCreateUpdateOfficeView(FilterListMixin,
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

    def get_mapped_query(self, request):
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

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
