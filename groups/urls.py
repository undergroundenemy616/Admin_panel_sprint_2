from groups import views
from django.urls import path

urlpatterns = [
    path('', views.ListCreateGroupAPIView.as_view()),
    path('/update', views.UpdateGroupUsersView.as_view())
]
