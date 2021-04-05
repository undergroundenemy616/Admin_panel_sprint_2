from django.urls import path

from bookings import views_actions

urlpatterns = [
    path('/<uuid:pk>', views_actions.ActionCancelBookingsView.as_view()),
]
