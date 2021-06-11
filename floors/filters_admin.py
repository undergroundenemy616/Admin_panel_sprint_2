import django_filters

from floors.models import Floor


class AdminFloorFilter(django_filters.FilterSet):
    room_type = django_filters.UUIDFilter('rooms__type', distinct=True)

    class Meta:
        model = Floor
        fields = ['office', 'room_type']
