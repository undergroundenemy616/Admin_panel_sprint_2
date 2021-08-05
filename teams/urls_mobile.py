from django.urls import path

from teams.views_mobile import MobileTeamViewSet

urlpatterns = [
    path('/<uuid:pk>', MobileTeamViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('', MobileTeamViewSet.as_view({'get': 'list', 'post': 'create'})),
]
