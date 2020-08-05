from files import views
from django.urls import path

urlpatterns = [
    path('', views.ListFiles.as_view())
]
