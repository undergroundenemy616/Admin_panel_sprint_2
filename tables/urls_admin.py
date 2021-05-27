from django.urls import path

from core.mapping import url_list, url_detail
from tables import views_admin

urlpatterns = [
    path('/tag', views_admin.AdminTableTagViewSet.as_view(url_list)),
    path('/tag/<uuid:pk>', views_admin.AdminTableTagViewSet.as_view(url_detail)),
    path('/marker', views_admin.AdminTableMarkerViewSet.as_view({'post': 'create'})),
    path('/marker/<int:pk>', views_admin.AdminTableMarkerViewSet.as_view({'delete': 'destroy', 'put': 'update'})),
    path('', views_admin.AdminTableViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminTableViewSet.as_view(url_detail)),
    path('/list_delete', views_admin.AdminTableListDeleteView.as_view()),
]
