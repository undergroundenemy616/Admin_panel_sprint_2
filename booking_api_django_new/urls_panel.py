from django.urls import path

from users import views as user_views
from bookings import views as booking_views

urlpatterns = [
    path('auth_kiosk', user_views.LoginOfficePanel.as_view()),
    path('refresh', user_views.RefreshTokenView.as_view()),
    path('book', booking_views.BookingsFromOfficePanelView.as_view())
    ]
