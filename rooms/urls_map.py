from django.urls import path

from rooms import views

urlpatterns = [
    path('', views.RoomMarkerView.as_view()),
]
