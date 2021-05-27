import django_filters

from room_types.models import RoomType


class AdminRoomTypeFilter(django_filters.FilterSet):

    class Meta:
        model = RoomType
        fields = ['office', 'bookable']
