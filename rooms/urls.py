from rooms import views
from django.urls import path

urlpatterns = [
    path('', views.ListHandler.as_view()),
    path('<int:pk>/', views.ObjectHandler.as_view())
]
