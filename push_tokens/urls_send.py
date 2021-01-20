from django.urls import path

from push_tokens import views

urlpatterns = [
    path('push', views.PushTokenSendSingleView.as_view()),
    path('broadcast', views.PushTokenSendBroadcastView.as_view()),
]
