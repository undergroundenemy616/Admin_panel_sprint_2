from django.urls import path

from core.mapping import url_detail, url_list
from groups import views_admin

urlpatterns = [
    path('/import_single', views_admin.AdminImportAccountsInGroupCsvView.as_view()),
    path('/import_list', views_admin.AdminImportAccountAndGroupsCsvView.as_view()),
    path('/import_titles', views_admin.AdminCreateGroupCsvView.as_view()),
    path('/access/<uuid:pk>', views_admin.AdminGroupAccessView.as_view()),
    path('', views_admin.AdminGroupViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminGroupViewSet.as_view(url_detail)),
]
