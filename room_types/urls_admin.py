from django.urls import path

from room_types import views_admin
from core.mapping import url_detail, url_list

urlpatterns = [
    path('', views_admin.AdminRoomTypeViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminRoomTypeViewSet.as_view(url_detail)),
]
