from bookings import views
from django.urls import path

urlpatterns = [
    path('', views.BookingsAdminView.as_view()),
    path('/fast', views.FastBookingAdminView.as_view())
]
