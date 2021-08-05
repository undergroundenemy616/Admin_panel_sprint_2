from django.urls import path

from core.mapping import url_detail, url_list
from offices import views_admin

urlpatterns = [
    path('', views_admin.AdminOfficeViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminOfficeViewSet.as_view(url_detail)),
]
