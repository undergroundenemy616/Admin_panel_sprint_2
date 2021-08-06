import django_filters

from group_bookings.models import GroupBooking


class AdminGroupBookingMeetingFilter(django_filters.FilterSet):
    table = django_filters.UUIDFilter('bookings__table')

    class Meta:
        model = GroupBooking
        fields = ['table']
