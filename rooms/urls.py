from rooms import views
from django.urls import path

urlpatterns = [
    path('/', views.RoomsView.as_view()),
    path('/room_markers', views.RoomMarkerView.as_view())
]
