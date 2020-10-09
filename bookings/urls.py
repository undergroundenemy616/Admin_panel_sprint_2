from bookings import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateBookingsView.as_view())
    # path(''),
    # path('int:pk/'),
    # path('fast'),
    # path('mobile'),
    # path('fast/mobile'),
    # path('operator'),
    # path('operator/fast'),
    # path('activate'),
    # path('deactivate'),
    # path('end'),
]
