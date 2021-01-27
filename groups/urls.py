from django.urls import path

from groups import views

urlpatterns = [
    path('', views.ListCreateGroupAPIView.as_view()),
    path('/update', views.UpdateUsersGroupView.as_view())
]
# TODO: import_single, import_titles, import_list
