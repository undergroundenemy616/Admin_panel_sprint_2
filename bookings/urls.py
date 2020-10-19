from bookings import views
from django.urls import path

urlpatterns = [
    path('', views.BookingsView.as_view()),
]
