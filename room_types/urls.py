from room_types import views
from django.urls import path

urlpatterns = [
    path('', views.CreateRoomTypesView.as_view()),
    path('<int:pk>/', views.ListUpdateDestroyRoomTypesView.as_view())
]
