from django.urls import include, path

from core.mapping import url_detail, url_list, url_list_with_delete
from users import views_admin as users_admin_view

urlpatterns = [
    path('/room', include('rooms.urls_admin')),
    path('/office_panel', users_admin_view.AdminOfficePanelViewSet.as_view(url_list)),
    path('/office_panel/<uuid:pk>', users_admin_view.AdminOfficePanelViewSet.as_view(url_detail)),
    path('/floor', include('floors.urls_admin')),

]
