import django_filters
from django_filters import Filter

from rooms.models import Room


class ListFilter(Filter):
    def filter(self, queryset, value):
        if not value:
            return queryset
        try:
            request = self.parent.request
        except AttributeError:
            return None
        values = request.query_params.getlist(self.label)
        return super(ListFilter, self).filter(queryset, values)


class AdminRoomFilter(django_filters.FilterSet):
    office = django_filters.UUIDFilter('floor__office')
    room_type = django_filters.UUIDFilter('type')
    bookable = django_filters.BooleanFilter('type__bookable')
    unified = django_filters.BooleanFilter('type__unified')
    images = django_filters.BooleanFilter('images', lookup_expr='isnull', exclude=True)
    type = django_filters.CharFilter('type__title')
    free = django_filters.NumberFilter('free', lookup_expr='gte')
    range_from = django_filters.NumberFilter('free', lookup_expr='gte')
    range_to = django_filters.NumberFilter('free', lookup_expr='lte')
    tags = ListFilter('tables__tags__title', lookup_expr='in', label='tags')
    office_panel = django_filters.BooleanFilter('floor__office_panels', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Room
        fields = ['office', 'floor', 'room_type', 'bookable', 'unified',
                  'type', 'zone', 'tags', 'office_panel']
