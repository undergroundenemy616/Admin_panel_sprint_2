from users import views
from django.urls import path

urlpatterns = [
    path('/auth', views.LoginOrRegisterUser.as_view()),
    path('/auth/admin/login', views.LoginStaff.as_view())
]
