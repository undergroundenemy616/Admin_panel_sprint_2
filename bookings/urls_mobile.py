from django.urls import path

from bookings.views_mobile import (MobileActionActivateBookingsView,
                                   MobileActionCancelBookingsView,
                                   MobileBookingListPersonalView,
                                   MobileBookingsView, MobileCancelBooking)
from rooms.views_mobile import SuitableRoomsMobileView

urlpatterns = [
    path('', MobileBookingsView.as_view()),
    path('/book_list/my', MobileBookingListPersonalView.as_view()),
    path('/<uuid:pk>', MobileActionCancelBookingsView.as_view()),
    path('/suitable_places', SuitableRoomsMobileView.as_view()),
    path('/cancel/<uuid:pk>', MobileCancelBooking.as_view()),
    path('/activate', MobileActionActivateBookingsView.as_view())
]
