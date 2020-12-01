from floors import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateDeleteFloorMapView.as_view()),
    path('/clean', views.CleanFloorMapView.as_view())
]
