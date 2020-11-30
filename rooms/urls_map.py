from rooms import views
from django.urls import path

urlpatterns = [
    path('', views.RoomMarkerView.as_view()),
]
