from django.urls import path

from floors.views_mobile import (MobileFloorMarkers, MobileListFloorMapView,
                                 MobileListFloorView, MobileSuitableFloorView)

urlpatterns = [
    path('', MobileListFloorView.as_view()),
    path('/<uuid:pk>/markers', MobileFloorMarkers.as_view()),
    path('/<uuid:pk>', MobileListFloorMapView.as_view()),
    path('/suitable', MobileSuitableFloorView.as_view())
]
