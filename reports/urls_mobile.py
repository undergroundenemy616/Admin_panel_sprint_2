from django.urls import path

from reports.views_mobile import MobileReportCreateView

urlpatterns = [
    path('', MobileReportCreateView.as_view()),
]
