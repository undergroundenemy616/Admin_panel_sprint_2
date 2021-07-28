import django_filters

from rooms.filters_admin import ListFilter
from users.models import Account


class AdminUserFilter(django_filters.FilterSet):
    group_exclude = django_filters.UUIDFilter('groups', exclude=True)
    group = django_filters.UUIDFilter('groups')
    users_exclude = ListFilter('id', lookup_expr='in', label='users_exclude', exclude=True)

    class Meta:
        model = Account
        fields = ['group_exclude', 'group', 'users_exclude']

