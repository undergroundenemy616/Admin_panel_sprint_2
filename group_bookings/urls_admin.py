from django.urls import path

from bookings.views_admin import (AdminGroupMeetingBookingViewSet,
                                  AdminGroupWorkplaceBookingViewSet,
                                  AdminGroupCombinedBookingSerializer, AdminTest)
from core.mapping import url_list

urlpatterns = [
    path('/meeting', AdminGroupMeetingBookingViewSet.as_view(url_list)),
    path('/meeting/<uuid:pk>', AdminGroupMeetingBookingViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('/workplace', AdminGroupWorkplaceBookingViewSet.as_view(url_list)),
    path('/workplace/<uuid:pk>', AdminGroupWorkplaceBookingViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('/combined', AdminGroupCombinedBookingSerializer.as_view()),
    path('/test', AdminTest.as_view())
]