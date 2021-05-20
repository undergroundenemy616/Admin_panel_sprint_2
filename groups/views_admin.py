from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from groups.filters_admin import AdminGroupFilter
from groups.models import Group
from groups.serializers_admin import (AdminGroupCreateSerializer,
                                      AdminGroupSerializer,
                                      AdminGroupUpdateSerializer,
                                      AdminGroupUserAccessSerializer, AdminImportAccountsInGroupCsvSerializer,
                                      AdminImportAccountAndGroupsCsvSerializer, AdminZoneForGroupSerializer,
                                      AdminCreateGroupCsvSerialzer)
from offices.models import Office


class AdminGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    permission_classes = (IsAdmin,)
    pagination_class = LimitStartPagination
    serializer_class = AdminGroupSerializer
    filterset_class = AdminGroupFilter

    def get_queryset(self, pk=None):
        if self.request.method == "GET":
            self.queryset = self.queryset.annotate(
                count=Count('accounts')
            )
        return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method == "GET" and self.request.query_params.get('user'):
            return AdminGroupUserAccessSerializer
        if self.request.method in "POST":
            return AdminGroupCreateSerializer
        if self.request.method == "PUT":
            return AdminGroupUpdateSerializer
        return self.serializer_class


class AdminGroupAccessView(GenericAPIView):
    queryset = Group.objects.all()
    permission_classes = (IsAdmin, )
    serializer_class = AdminZoneForGroupSerializer

    def get(self, request, pk=None, *args, **kwargs):
        return Response(self.serializer_class(instance=Office.objects.filter(zones__groups=pk).distinct(), many=True,
                                              context={'group_id': pk}).data, status=status.HTTP_200_OK)


class AdminImportAccountsInGroupCsvView(GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = AdminImportAccountsInGroupCsvSerializer
    pagination_class = None
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(group, status=status.HTTP_200_OK)


class AdminImportAccountAndGroupsCsvView(GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = AdminImportAccountAndGroupsCsvSerializer
    pagination_class = None
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        groups = serializer.save()
        return Response(groups, status=status.HTTP_200_OK)


class AdminCreateGroupCsvView(GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = AdminCreateGroupCsvSerialzer
    pagination_class = None
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        groups = serializer.save()
        return Response(groups, status=status.HTTP_200_OK)
