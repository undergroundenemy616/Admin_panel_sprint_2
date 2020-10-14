from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response


class FilterListMixin(ListModelMixin):
    def list(self, request, *args, **kwargs):
        """Provides filtered list interface."""
        mapped = self.get_mapped_query(request)
        queryset = self.get_queryset()
        if mapped:
            queryset = queryset.filter(**mapped)

        queryset = self.filter_queryset(queryset)  # django filtering
        page = self.paginate_queryset(queryset)  # rest page pagination

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)  # rest response by pagination
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_mapped_query(self, *args, **kwargs):
        """Method must be implemented!"""
        raise NotImplementedError
