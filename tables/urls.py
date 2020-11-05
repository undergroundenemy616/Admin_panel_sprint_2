from tables import views
from django.urls import path

urlpatterns = [
    path('', views.TableView.as_view()),
    path('/<uuid:pk>', views.DetailTableView.as_view()),
    path('/table_tag/<uuid:pk>', views.TableTagView.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'})),
]
