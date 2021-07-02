from django.urls import path

from bookings import views_admin
from bookings.views_admin import AdminGroupMeetingBookingViewSet, AdminGroupWorkplaceBookingViewSet
from core.mapping import url_detail, url_list

urlpatterns = [
    path('/dashboard', views_admin.AdminBookingStatisticsDashboardView.as_view()),
    path('/employee_stats', views_admin.AdminBookingEmployeeStatisticsView.as_view()),
    path('/future', views_admin.AdminBookingFutureStatisticsView.as_view()),
    path('/room_type_stats', views_admin.AdminBookingRoomTypeStatisticsView.as_view()),
    path('', views_admin.AdminBookingViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminBookingViewSet.as_view(url_detail)),
    path('/meeting', AdminGroupMeetingBookingViewSet.as_view(url_list)),
    path('/meeting/<uuid:pk>', AdminGroupMeetingBookingViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('/workplace', AdminGroupWorkplaceBookingViewSet.as_view(url_list)),
    path('/workplace/<uuid:pk>', AdminGroupWorkplaceBookingViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}))
]
