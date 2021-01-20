from django.urls import path

from floors import views

urlpatterns = [
    path('', views.ListCreateFloorView.as_view()),
    path('/<uuid:pk>', views.RetrieveUpdateDeleteFloorView.as_view()),
]
