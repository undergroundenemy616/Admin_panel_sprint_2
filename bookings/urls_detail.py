from bookings import views
from django.urls import path

urlpatterns = [
    path('<uuid:pk>/', views.ActionCancelBookingsView.as_view()),
]
