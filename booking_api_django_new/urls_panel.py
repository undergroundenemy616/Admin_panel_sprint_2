from django.urls import path, include

from floors import views_panel as floor_views
from rooms import views_panel as room_views
from users import views as user_views
from users import views_panel as user_panel_views

urlpatterns = [
    path('/auth_kiosk', user_views.LoginOfficePanel.as_view()),
    path('/refresh', user_views.RefreshTokenView.as_view()),
    path('/book', include('bookings.urls')),
    path('/floor', floor_views.PanelListFloorView.as_view()),
    path('/room', room_views.PanelRoomsView.as_view()),
    path('/register_user', user_panel_views.PanelRegisterUserView.as_view()),
    path('/auth', user_views.LoginOrRegisterUserFromMobileView.as_view()),
    ]
