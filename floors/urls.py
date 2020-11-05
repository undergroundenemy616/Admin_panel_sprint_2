from floors import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateFloorView.as_view()),
    path('/<uuid:pk>', views.RetrieveUpdateDeleteFloorView.as_view()),
]
