from django.urls import path

from reports.views_mobile import MobileReportCreateView, MobileRequestDemoView

urlpatterns = [
    path('', MobileReportCreateView.as_view()),
    path('/request_demo', MobileRequestDemoView.as_view()),
]
