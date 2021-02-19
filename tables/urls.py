from django.urls import path

from tables import views

urlpatterns = [
    path('', views.TableView.as_view()),
    path('/list_create', views.ListCreateTableCsvView.as_view()),
]
