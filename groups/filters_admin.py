import django_filters

from groups.models import Group


class AdminGroupFilter(django_filters.FilterSet):
    user = django_filters.UUIDFilter('accounts')

    class Meta:
        model = Group
        fields = ['user']
