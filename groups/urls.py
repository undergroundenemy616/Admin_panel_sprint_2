from django.urls import path

from groups import views

urlpatterns = [
    path('', views.ListCreateGroupAPIView.as_view()),
    path('/update', views.UpdateUsersGroupView.as_view()),
    path('/import_titles', views.ListCreateGroupCsvAPIView.as_view()),
    path('/import_list', views.ListCreateGroupWithAccountsCsvAPIView.as_view()),
    path('/import_single', views.ListCreateGroupOnlyAccountsCsvAPIView.as_view())
]
