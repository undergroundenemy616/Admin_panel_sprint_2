from django.urls import path

from bookings import views

urlpatterns = [
    path('/user', views.BookingsListUserView.as_view()),
    path('/table', views.BookingListTablesView.as_view()),
    path('/my', views.BookingListPersonalView.as_view()),
    path('/office', views.BookingsListOfficeView.as_view()),
    path('/type', views.BookingsListTypeView.as_view())
]
