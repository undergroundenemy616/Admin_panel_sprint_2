from rooms import views
from django.urls import path

urlpatterns = [
    path('', views.ListRooms.as_view())
]
