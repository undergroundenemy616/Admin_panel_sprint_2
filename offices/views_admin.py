from django.db.models import Count, Prefetch, Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status, viewsets

from core.handlers import ResponseException
from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from groups.models import Group
from offices.filters_admin import AdminOfficeZoneFilter
from offices.models import Office, OfficeZone
from offices.serializers_admin import (AdminOfficeCreateSerializer,
                                       AdminOfficeSerializer,
                                       AdminOfficeZoneCreateSerializer,
                                       AdminOfficeZoneSerializer,
                                       AdminOfficeZoneUpdateSerializer,
                                       AdminOfficeSingleSerializer)


class AdminOfficeViewSet(viewsets.ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = AdminOfficeSerializer
    pagination_class = LimitStartPagination
    permission_classes = (IsAdmin,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        if self.request.method != "POST":
            self.queryset = self.queryset.annotate(
                capacity=Count('floors__rooms__tables'),
                occupied=Count('floors__rooms__tables', filter=Q(floors__rooms__tables__is_occupied=True)),
                capacity_meeting=Count('floors__rooms__tables', filter=Q(floors__rooms__type__unified=True)),
                occupied_meeting=Count('floors__rooms__tables', filter=Q(floors__rooms__type__unified=True) &
                                                                       Q(floors__rooms__tables__is_occupied=True)),
                capacity_tables=Count('floors__rooms__tables', filter=Q(floors__rooms__type__unified=False)),
                occupied_tables=Count('floors__rooms__tables', filter=Q(floors__rooms__type__unified=False) &
                                                                      Q(floors__rooms__tables__is_occupied=True))
            ).prefetch_related('floors').select_related('license')
        return self.queryset

    def get_serializer_class(self):
        if self.kwargs.get('pk'):
            return AdminOfficeSingleSerializer
        if self.request.method == "POST":
            return AdminOfficeCreateSerializer
        return self.serializer_class


class AdminOfficeZoneViewSet(viewsets.ModelViewSet):
    queryset = OfficeZone.objects.all()
    serializer_class = AdminOfficeZoneSerializer
    pagination_class = LimitStartPagination
    permission_classes = (IsAdmin,)
    filterset_class = AdminOfficeZoneFilter

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.prefetch_related(Prefetch("groups", queryset=Group.objects.all().annotate(
                count=Count('accounts')
            )))
        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminOfficeZoneCreateSerializer
        if self.request.method == "PUT":
            return AdminOfficeZoneUpdateSerializer
        return self.serializer_class

    def perform_destroy(self, instance):
        if not instance.is_deletable:
            raise ResponseException(detail="Can't delete predefined office")
        return super(AdminOfficeZoneViewSet, self).perform_destroy(instance)

    def get_object(self):
        instance = super(AdminOfficeZoneViewSet, self).get_object()
        if not instance.is_deletable and self.request.method != "GET":
            raise ResponseException(detail="Can't edit or delete predefined zone")
        return instance
