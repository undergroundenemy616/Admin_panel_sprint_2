from push_tokens import views
from django.urls import path

urlpatterns = [
    path('push', views.PushTokenSendSingleView.as_view()),
    path('broadcast', views.PushTokenSendBroadcastView.as_view()),
]
