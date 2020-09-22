from rooms import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateRoomsView.as_view()),
    path('<int:pk>/', views.RetrieveUpdateRoomsView.as_view())
]
