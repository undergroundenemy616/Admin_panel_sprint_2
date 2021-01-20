from django.urls import path

from rooms import views

urlpatterns = [
    path('/<uuid:pk>', views.DetailRoomView.as_view())
]
