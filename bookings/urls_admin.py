from django.urls import path

from bookings import views_admin
from core.mapping import url_detail, url_list

urlpatterns = [
    path('', views_admin.AdminBookingViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminBookingViewSet.as_view(url_detail)),
]
