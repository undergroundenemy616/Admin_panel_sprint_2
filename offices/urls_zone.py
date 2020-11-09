from offices import views
from django.urls import path

urlpatterns = [
    path('', views.ListOfficeZoneView.as_view())
]
