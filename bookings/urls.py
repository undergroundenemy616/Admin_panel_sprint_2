from bookings import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateBookingsView.as_view()),
    path('slots', views.ActionCheckAvailableSlotsView.as_view()),
    path('activate', views.ActionActivateBookingsView.as_view()),
    path('deactivate', views.ActionDeactivateBookingsView.as_view()),
    path('end', views.ActionEndBookingsView.as_view()),
    path('fast', views.CreateFastBookingsView.as_view()),

    # path('int:pk/'),
    # path('mobile'),
    # path('fast/mobile'),
    # path('operator'),
    # path('operator/fast'),
]
