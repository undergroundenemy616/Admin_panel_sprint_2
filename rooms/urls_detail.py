from rooms import views
from django.urls import path

urlpatterns = [
    path('/<uuid:pk>', views.DetailRoomView.as_view())
]
