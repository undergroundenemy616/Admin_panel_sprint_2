import django_filters

from bookings.models import Booking


class AdminBookingFilter(django_filters.FilterSet):
    room = django_filters.UUIDFilter('table__room')
    floor = django_filters.UUIDFilter('table__room__floor')
    office = django_filters.UUIDFilter('table__room__floor__office')
    unified = django_filters.BooleanFilter('table__room__type__unified')

    class Meta:
        model = Booking
        fields = ['user', 'table', 'room', 'floor', 'office', 'unified']
