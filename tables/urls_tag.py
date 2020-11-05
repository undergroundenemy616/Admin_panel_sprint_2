from tables import views
from django.urls import path

urlpatterns = [
    path('', views.TableTagView.as_view({
        'get': 'list',
        'post': 'create'})),
    path('/<uuid:pk>', views.TableTagView.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'})),
]
