from tables import views
from django.urls import path

urlpatterns = [
    path('', views.TableView.as_view({
        'get': 'list',
        'post': 'create'})),
    path('<int:pk>/', views.TableView.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'}))
]
