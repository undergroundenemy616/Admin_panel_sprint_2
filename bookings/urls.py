from django.urls import path

from bookings import views
from bookings import views_statistics
from bookings import views_statistics_FD

urlpatterns = [
    path('', views.BookingsView.as_view()),
    path('/slots', views.ActionCheckAvailableSlotsView.as_view()),
    path('/activate', views.ActionActivateBookingsView.as_view()),
    path('/deactivate', views.ActionDeactivateBookingsView.as_view()),
    path('/end', views.ActionEndBookingsView.as_view()),
    path('/fast', views.CreateFastBookingsView.as_view()),
    path('/room_type_stats', views_statistics.BookingStatisticsRoomTypes.as_view()),
    path('/employee_stats', views_statistics.BookingEmployeeStatistics.as_view()),
    path('/future', views_statistics_FD.BookingFuture.as_view()),
    path('/dashboard', views_statistics_FD.BookingStatisticsDashboard.as_view()),
    path('/from_panel', views.BookingsFromOfficePanelView.as_view())
]
