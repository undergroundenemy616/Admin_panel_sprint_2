from bookings import views
from django.urls import path

urlpatterns = [
<<<<<<< HEAD
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
=======
    # path('int:pk/', views.SingleBookingView.as_view()),
>>>>>>> 56de13811ec61eca1c84471f02624700dfe57830
]
