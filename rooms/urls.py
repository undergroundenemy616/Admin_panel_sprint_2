from rooms import views
from room_types import views as type_view
from django.urls import path

urlpatterns = [
    path('', views.RoomsView.as_view()),
    path('/type', type_view.ListCreateRoomTypesView.as_view()),
    path('/type/<uuid:pk>', type_view.UpdateDestroyRoomTypesView.as_view())
]
