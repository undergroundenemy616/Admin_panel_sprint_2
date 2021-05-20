from django.urls import path

from rooms.views_mobile import MobileRoomViewSet

urlpatterns = [
    path('/<uuid:pk>', MobileRoomViewSet.as_view({'get': 'retrieve'}))
]
