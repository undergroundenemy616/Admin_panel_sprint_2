from django.urls import path
from core.mapping import url_detail, url_list
from clients import views

urlpatterns = [
    path('', views.ClientViewSet.as_view(url_list)),
    path('/<int:pk>', views.ClientViewSet.as_view(url_detail))
]
