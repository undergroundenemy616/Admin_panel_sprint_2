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
    # path('groups/', include('groups.urls'))
    '''
    __AUTH__
    [] /auth
    [] /refresh
    [] /auth_employee
    [] /register_employee
    [] /register_user
    [] /register_kiosk
    [] /register_kiosk/<id>
    [] /auth_kiosk
    [] /account
    [] /accounts_list
    [] /accounts/<id>
    [] /account_confirm
    [] /groups
    [] /group/<id>
    [] /groups/update
    [] /groups/import_single
    [] /groups/import_list
    [] /groups/import_titles
    [] /enter
    [] /service/email
    [] /pass_change
    [] /pass_reset
    [] /operator_promotion
    
    
    [] /files
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
    '''
]
