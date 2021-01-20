from django.urls import path

from bookings import views

urlpatterns = [
    path('/active', views.BookingsActiveListView.as_view()),
    path('/user', views.BookingsUserListView.as_view()),
    path('/table', views.BookingListTablesView.as_view()),
    path('/my', views.BookingListPersonalView.as_view()),
]
