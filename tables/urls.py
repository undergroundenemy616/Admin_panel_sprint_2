from tables import views
from django.urls import path

urlpatterns = [
    path('', views.TableView.as_view()),
]
