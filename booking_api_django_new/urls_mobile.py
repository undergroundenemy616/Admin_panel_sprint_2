from django.urls import include, path

from users.views_mobile import MobileFirstCheckView

urlpatterns = [
    path('', MobileFirstCheckView.as_view()),
    path('/booking', include('bookings.urls_mobile')),
    path('/file', include('files.urls_mobile')),
    path('/floor', include('floors.urls_mobile')),
    path('/office', include('offices.urls_mobile')),
    path('/report', include('reports.urls_mobile')),
    path('/table', include('tables.urls_mobile')),
    path('/user', include('users.urls_mobile')),
    path('/room', include('rooms.urls_mobile'))
]
