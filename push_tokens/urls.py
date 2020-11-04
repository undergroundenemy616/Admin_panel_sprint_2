from push_tokens import views
from django.urls import path

urlpatterns = [
    path('', views.PushTokenView.as_view()),
]
