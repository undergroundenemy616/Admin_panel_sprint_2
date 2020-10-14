from rooms import views
from django.urls import path

urlpatterns = [
    path('', views.RoomsView.as_view())
]
