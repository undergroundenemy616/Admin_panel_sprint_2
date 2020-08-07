from offices import views
from django.urls import path

urlpatterns = [
    path('', views.ListOffices.as_view())
]
