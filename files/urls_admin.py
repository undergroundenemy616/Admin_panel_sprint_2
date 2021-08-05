from django.urls import path

from files import views_admin

urlpatterns = [
    path('', views_admin.AdminCreateFilesView.as_view()),
    path('/map', views_admin.AdminFileWebpCreateView.as_view())
]
