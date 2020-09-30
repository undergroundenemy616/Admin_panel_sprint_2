from floors import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateFloorView.as_view()),
    path('<int:pk>/', views.RetrieveUpdateDeleteFloorView.as_view()),
    path('floormaps/', views.ListCreateFloorMapView.as_view()),  # todo another app or routes
]
