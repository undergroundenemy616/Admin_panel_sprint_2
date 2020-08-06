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
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('files/', include('files.urls')),
    path('tables/', include('tables.urls'))
    # path('groups/', include('groups.urls'))
]

'''
__AUTH__
[POST] /auth
[POST] /refresh
[POST] /auth_employee
[POST] /register_employee
[POST] /register_user
[POST] /register_guest
[POST] /register_kiosk
[PUT] /register_kiosk/<id>
[POST] /auth_kiosk
[GET] /account
[GET] /accounts_list
[PUT, DELETE] /accounts/<id>
[POST] /account_confirm
[GET, POST, PUT, DELETE] /groups
[] /group/<id>
[PUT] /groups/update
[POST] /groups/import_single
[] /groups/import_list
[] /groups/import_titles
[POST] /enter
[POST] /service/email
[POST] /pass_change
[POST] /pass_reset
[POST] /operator_promotion

__BOOKINGS__
[] /office
[] /offices/<id>
[] /zone
[] /zones/<id>
[] /floor
[] /floor/<id>
[] /room
[] /rooms/<id>
[] /table_tag
[] /table_tags/<id>
[] /table
[] /tables/<id>
[] /floor_map
[] /floor_map/clear
[] /room_map
[] /table/rate
[] /table/activate
[] /table/receive
[] /table_status_receive
[] /feedback

__FILE__
[] /files
'''
