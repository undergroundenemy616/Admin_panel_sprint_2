from django.urls import path

from bookings import views
from bookings import views_actions
from bookings import views_statistics

urlpatterns = [
    path('', views.BookingsView.as_view()),
    path('/slots', views_actions.ActionCheckAvailableSlotsView.as_view()),
    path('/activate', views_actions.ActionActivateBookingsView.as_view()),
    path('/deactivate', views_actions.ActionDeactivateBookingsView.as_view()),
    path('/end', views_actions.ActionEndBookingsView.as_view()),
    path('/fast', views.CreateFastBookingsView.as_view()),
    path('/room_type_stats', views_statistics.BookingStatisticsRoomTypes.as_view()),
    path('/employee_stats', views_statistics.BookingEmployeeStatistics.as_view()),
    path('/future', views_statistics.BookingFuture.as_view()),
    path('/dashboard', views_statistics.BookingStatisticsDashboard.as_view())
]
