import datetime

import django_filters
from django.db.models import Q

from core.handlers import ResponseException
from tables.models import Table, TableTag


class AdminTableFilter(django_filters.FilterSet):

    class Meta:
        model = Table
        fields = ['room']

    def filter_queryset(self, queryset):
        date_from, date_to = None, None

        if self.request.query_params.get('date_from') and self.request.query_params.get('date_to'):
            try:
                date_from = datetime.datetime.strptime(self.request.query_params.get('date_from'), '%Y-%m-%dT%H:%M:%S')
                date_to = datetime.datetime.strptime(self.request.query_params.get('date_to'), '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise ResponseException("Wrong date format")

        if date_from and date_to:
            queryset = queryset.exclude(
                        (Q(existing_bookings__date_from__gte=date_from) & Q(existing_bookings__date_from__lt=date_to))
                        |
                        (Q(existing_bookings__date_from__lte=date_from) & Q(existing_bookings__date_to__gte=date_to))
                        |
                        (Q(existing_bookings__date_to__gt=date_from) & Q(existing_bookings__date_to__lte=date_to))
                )
        return super(AdminTableFilter, self).filter_queryset(queryset=queryset)


class AdminTableTagFiler(django_filters.FilterSet):

    class Meta:
        model = TableTag
        fields = ['office']
