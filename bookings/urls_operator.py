from django.urls import path

from bookings import views

urlpatterns = [
    path('', views.BookingsAdminView.as_view()),
    path('/fast', views.FastBookingAdminView.as_view())
]
