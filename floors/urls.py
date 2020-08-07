from floors import views
from django.urls import path

urlpatterns = [
    path('', views.ListFloors.as_view())
]
