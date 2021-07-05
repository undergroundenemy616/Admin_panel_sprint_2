from django.urls import path

from bookings.views_mobile import MobileGroupMeetingBookingViewSet, MobileGroupWorkplaceBookingViewSet
from core.mapping import url_list

urlpatterns = [
    path('/meeting', MobileGroupMeetingBookingViewSet.as_view(url_list)),
    path('/meeting/<uuid:pk>', MobileGroupMeetingBookingViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('/workplace', MobileGroupWorkplaceBookingViewSet.as_view(url_list)),
    path('/workplace/<uuid:pk>', MobileGroupWorkplaceBookingViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}))
]