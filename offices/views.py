from rest_framework import status
from rest_framework.response import Response
from core.pagination import DefaultPagination
from offices.models import Office
from offices.serializers import CreateOfficeSerializer
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
    serializer_class = CreateOfficeSerializer
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
