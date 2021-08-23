from django.urls import include, path

from bookings import views_panel as bookings_views
from floors import views_panel as floor_views
from rooms import views_panel as room_views
from users import views as user_views

urlpatterns = [
    path('/auth_kiosk', user_views.LoginOfficePanel.as_view()),
    path('/refresh', user_views.RefreshTokenView.as_view()),
    path('/book', include('bookings.urls')),
    path('/floor', floor_views.PanelListFloorView.as_view()),
    path('/room', room_views.PanelRoomsView.as_view()),
    path('/register_user', user_views.RegisterUserFromAdminPanelView.as_view()),
    path('/auth', user_views.LoginOrRegisterUserFromMobileView.as_view()),
    path('/single/auth_user', user_views.LoginOrRegisterUserFromPanelView.as_view()),
    path('/single/room', room_views.PanelSingleRoomView.as_view()),
    path('/single/book', bookings_views.PanelSingleBookingView.as_view()),
    ]
