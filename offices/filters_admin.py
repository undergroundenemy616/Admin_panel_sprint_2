import django_filters

from offices.models import OfficeZone


class AdminOfficeZoneFilter(django_filters.FilterSet):

    class Meta:
        model = OfficeZone
        fields = ['office']
