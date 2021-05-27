from django.urls import path

from push_tokens import views_admin as views

urlpatterns = [
    path('/group', views.AdminPushGroupView.as_view()),
    path('/user', views.AdminPushUserView.as_view()),
    path('/send_broadcast', views.AdminSendPushView.as_view())
]
