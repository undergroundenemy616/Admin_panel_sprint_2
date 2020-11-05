from tables import views
from django.urls import path

urlpatterns = [
    path('', views.TableView.as_view()),
    path('/<uuid:pk>', views.DetailTableView.as_view()),
]
