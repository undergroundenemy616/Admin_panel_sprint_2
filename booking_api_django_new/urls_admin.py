from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.mapping import url_detail, url_list, url_list_with_delete
from offices import views_admin as office_admin_view
from users import views_admin as users_admin_view
from floors import views_admin as floor_admin_view
from tables import views_admin as table_admin_view

office_zone_router = DefaultRouter(trailing_slash=False)
office_zone_router.register('', office_admin_view.AdminOfficeZoneViewSet)

urlpatterns = [
    path('/auth', users_admin_view.AdminLoginView.as_view()),
    path('/room', include('rooms.urls_admin')),
    path('/table', include('tables.urls_admin')),
    path('/room_type', include('room_types.urls_admin')),
    path('/user', include('users.urls_admin')),
    path('/license', include('licenses.urls_admin')),
    path('/file', include('files.urls_admin')),
    path('/office', include('offices.urls_admin')),
    path('/booking', include('bookings.urls_admin')),
    path('/office_panel', users_admin_view.AdminOfficePanelViewSet.as_view(url_list)),
    path('/office_panel/<uuid:pk>', users_admin_view.AdminOfficePanelViewSet.as_view(url_detail)),
    path('/floor', include('floors.urls_admin')),
    path('/group', include('groups.urls_admin')),
    path('/group_booking', include('group_bookings.urls_mobile')),
    path('/office_zone', office_admin_view.AdminOfficeZoneViewSet.as_view(url_list)),
    path('/office_zone/<uuid:pk>', office_admin_view.AdminOfficeZoneViewSet.as_view(url_detail)),
    path('/floor_map', floor_admin_view.AdminFloorMapViewSet.as_view(url_list)),
    path('/floor_map/<uuid:pk>', floor_admin_view.AdminFloorMapViewSet.as_view(url_detail)),
    path('/push', include('push_tokens.urls_admin'))

]
