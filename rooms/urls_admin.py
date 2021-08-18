from django.urls import path

from core.mapping import url_list, url_detail
from rooms import views_admin

urlpatterns = [
    path('/marker', views_admin.AdminRoomMarkerViewSet.as_view({'post': 'create'})),
    path('/marker/<int:pk>', views_admin.AdminRoomMarkerViewSet.as_view({'delete': 'destroy', 'put': 'update'})),
    path('', views_admin.AdminRoomViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminRoomViewSet.as_view(url_detail)),
    path('/list_delete', views_admin.AdminRoomListDeleteView.as_view()),
    path('/exchange', views_admin.AdminRoomExchangeView.as_view())
]
