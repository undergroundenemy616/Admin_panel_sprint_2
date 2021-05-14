"""booking_api_django_new URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from typing import Any

from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users import views
from tables.views import TableSlotsView
from users.views import custom404

handler404 = custom404

def get_swagger() -> Any:
    """Returns current swagger class from `drf_yasg`"""
    swagger = get_schema_view(
        openapi.Info(
            title="SimpleOffice API",
            default_version='a-1.0',
            description="Test description",
            terms_of_service="https://www.google.com/policies/terms/",
            contact=openapi.Contact(email="support@liis.su"),
            license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,)
    )
    return swagger


schema_view = get_swagger()

urlpatterns = [
    # Swagger tools
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^docs/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Current urls
    path('auth', views.LoginOrRegisterUserFromMobileView.as_view()),
    path('auth_employee', views.LoginStaff.as_view()),
    path('auth_kiosk', views.LoginOfficePanel.as_view()),
    path('refresh', views.RefreshTokenView.as_view()),
    path('register_user', views.RegisterUserFromAdminPanelView.as_view()),
    path('register_employee', views.RegisterStaffView.as_view()),
    path('register_kiosk', views.OfficePanelRegister.as_view()),
    path('register_kiosk/<uuid:pk>', views.OfficePanelUpdate.as_view()),
    path('account', views.AccountView.as_view()),
    path('accounts/<uuid:pk>', views.SingleAccountView.as_view()),
    path('accounts_list', views.AccountListView.as_view()),
    path('accounts_first/<uuid:pk>', views.AccountFirstPutView.as_view()),
    path('service_email', views.ServiceEmailView.as_view()),
    path('user_access/<uuid:pk>', views.UserAccessView.as_view()),
    path('operator_promotion', views.OperatorPromotionView.as_view()),
    path('enter', views.EntranceCollectorView.as_view()),
    path('report', include('reports.urls')),
    path('group_access', include('offices.urls_group_access')),
    path('group', include('groups.urls_detail')),
    path('groups', include('groups.urls')),
    path('files', include('files.urls')),
    path('table_tag', include('tables.urls_tag')),
    path('table_tags', include('tables.urls_detail_tag')),
    path('license', include('licenses.urls')),
    path('table', include('tables.urls')),
    path('tables', include('tables.urls_detail')),
    path('table_slots/<uuid:pk>', TableSlotsView.as_view()),
    path('room_map', include('rooms.urls_map')),
    path('table_markers', include('tables.urls_marker')),
    path('room/type', include('room_types.urls')),
    path('room', include('rooms.urls')),
    path('rooms', include('rooms.urls_detail')),
    path('floor', include('floors.urls')),
    path('floor_map', include('floors.urls_map')),
    path('office', include('offices.urls')),
    path('offices', include('offices.urls_detail')),
    path('zone', include('offices.urls_zone')),
    path('zones', include('offices.urls_zones')),
    path('book', include('bookings.urls')),
    path('books', include('bookings.urls_detail')),
    path('book_operator', include('bookings.urls_operator')),
    path('book_list', include('bookings.urls_list')),
    path('tokens', include('push_tokens.urls')),
    path('send_', include('push_tokens.urls_send')),
    path('pass_change', views.PasswordChangeView.as_view()),
    path('pass_reset', views.PasswordResetView.as_view()),
    path('panel', include('booking_api_django_new.urls_panel')),
    path('mobile', include('booking_api_django_new.urls_mobile')),
    path('admin', include('booking_api_django_new.urls_admin'))
]
