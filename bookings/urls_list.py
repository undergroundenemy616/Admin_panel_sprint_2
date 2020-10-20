from bookings import views
from django.urls import path

urlpatterns = [
    path('/active', views.BookingsActiveListView.as_view()),
    path('/user', views.BookingsUserListView.as_view()),
    path('/table', views.BookingListTablesView.as_view()),
    path('/my', views.BookingListPersonalView.as_view()),
]
