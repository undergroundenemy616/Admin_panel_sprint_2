from django.urls import path

from licenses import views_admin

urlpatterns = [
    path('', views_admin.AdminListLicensesView.as_view()),
]
