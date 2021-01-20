from django.urls import path

from offices import views

urlpatterns = [
    path('', views.ListCreateUpdateOfficeView.as_view()),
]
