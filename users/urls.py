from users import views
from django.urls import path

urlpatterns = [
    path('auth/', views.LoginOrRegister.as_view()),
]
