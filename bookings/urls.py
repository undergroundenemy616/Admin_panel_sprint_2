from django.urls import path

from bookings import views

urlpatterns = [
    path('', views.BookingsView.as_view()),
    path('/slots', views.ActionCheckAvailableSlotsView.as_view()),
    path('/activate', views.ActionActivateBookingsView.as_view()),
    path('/deactivate', views.ActionDeactivateBookingsView.as_view()),
    path('/end', views.ActionEndBookingsView.as_view()),
    path('/fast', views.CreateFastBookingsView.as_view()),
    path('/room_type_stats', views.BookingStatisticsRoomTypes.as_view()),
    path('/employee_stats', views.BookingEmployeeStatistics.as_view()),
    path('/future', views.BookingFuture.as_view()),
    path('/dashboard', views.BookingStatisticsDashboard.as_view())
]
