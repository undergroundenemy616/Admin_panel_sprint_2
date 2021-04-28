from django.urls import path

from bookings import views

urlpatterns = [
    path('/<uuid:pk>', views.ActionCancelBookingsView.as_view()),
]
