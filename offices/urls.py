from offices import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateUpdateOfficeView.as_view()),
    path('<int:pk>/', views.RetrieveUpdateDeleteOfficeView.as_view())
]
