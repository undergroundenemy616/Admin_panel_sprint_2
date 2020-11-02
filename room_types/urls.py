from room_types import views
from django.urls import path


# Moved to rooms urls
urlpatterns = [
    path('', views.ListCreateRoomTypesView.as_view()),
    path('/<uuid:pk>', views.UpdateDestroyRoomTypesView.as_view())
]
