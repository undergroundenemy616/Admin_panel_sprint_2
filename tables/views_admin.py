from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.handlers import ResponseException
from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from tables.filters_admin import AdminTableFilter, AdminTableTagFiler
from tables.models import Table, TableTag
from tables.serializers_admin import (AdminTableListDeleteSerializer,
                                      AdminTableSerializer,
                                      AdminTableTagCreateSerializer,
                                      AdminTableTagSerializer, AdminTableCreateUpdateSerializer)


class AdminTableListDeleteView(GenericAPIView):
    serializer_class = AdminTableListDeleteSerializer
    permission_classes = (IsAdmin, )

    def delete(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminTableTagViewSet(viewsets.ModelViewSet):
    queryset = TableTag.objects.all()
    permission_classes = (IsAdmin, )
    serializer_class = AdminTableTagSerializer
    pagination_class = LimitStartPagination
    filterset_class = AdminTableTagFiler

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminTableTagCreateSerializer
        return self.serializer_class

    def get_queryset(self):
        return self.queryset.select_related('icon')

    def destroy(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            return super(AdminTableTagViewSet, self).destroy(request, *args, **kwargs)
        if request.data.get('table_tags'):
            tags = TableTag.objects.filter(id__in=request.data.get('table_tags'))
            for tag in tags:
                self.perform_destroy(tag)
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ResponseException("Nothing to delete")


class AdminTableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = AdminTableSerializer
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination
    filterset_class = AdminTableFilter

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.select_related(
                'table_marker', 'room', 'room__floor').prefetch_related('images', 'tags', 'tags__icon')
        return self.queryset

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT"]:
            return AdminTableCreateUpdateSerializer
        return self.serializer_class
