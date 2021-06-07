from django.urls import path

from room_types import views as type_view
from rooms import views

urlpatterns = [
    path('', views.RoomsView.as_view()),
    path('/type', type_view.ListCreateRoomTypesView.as_view()),
    path('/type/<uuid:pk>', type_view.UpdateDestroyRoomTypesView.as_view()),
    path('/list_create', views.ListCreateRoomCsvView.as_view())
]
