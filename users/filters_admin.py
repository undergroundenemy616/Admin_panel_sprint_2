import django_filters

from users.models import Account


class AdminUserFilter(django_filters.FilterSet):
    group_exclude = django_filters.UUIDFilter('groups', exclude=True)
    group = django_filters.UUIDFilter('groups')

    class Meta:
        model = Account
        fields = ['group_exclude', 'group']

