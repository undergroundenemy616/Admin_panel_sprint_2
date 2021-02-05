from django.urls import path

from reports import views

urlpatterns = [
    path('', views.ReportCreateView.as_view()),
    path('/history', views.ReportHistoryView.as_view()),
]
