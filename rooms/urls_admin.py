from django.urls import path

from core.mapping import url_list, url_detail
from rooms import views_admin

urlpatterns = [
    path('', views_admin.AdminRoomViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminRoomViewSet.as_view(url_detail)),
    path('/list_delete', views_admin.AdminRoomListDeleteView.as_view()),
]
