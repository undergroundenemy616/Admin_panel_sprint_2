from django.urls import path

from offices import views

urlpatterns = [
    path('', views.ListOfficeZoneView.as_view())
]
