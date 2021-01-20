from django.urls import path

from push_tokens import views

urlpatterns = [
    path('', views.PushTokenView.as_view()),
]
