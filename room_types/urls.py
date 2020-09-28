from room_types import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateRoomTypesView.as_view()),
    path('<int:pk>/', views.UpdateDestroyRoomTypesView.as_view())
]
