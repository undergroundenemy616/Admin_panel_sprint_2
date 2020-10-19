from rooms import views
from django.urls import path

urlpatterns = [
    path('/<int:pk>', views.DetailRoomView.as_view())
]
