from django.urls import path

from users import views

urlpatterns = [
    path('auth_kiosk', views.LoginOfficePanel.as_view()),
    path('refresh', views.RefreshTokenView.as_view()),
    path()
    ]
