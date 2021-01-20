from django.urls import path

from floors import views

urlpatterns = [
    path('', views.ListCreateDeleteFloorMapView.as_view()),
    path('/clean', views.CleanFloorMapView.as_view())
]
