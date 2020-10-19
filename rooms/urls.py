from rooms import views
from django.urls import path

urlpatterns = [
    path('room_markers/', views.RoomMarkerView.as_view()),
    path('', views.RoomsView.as_view())
]
