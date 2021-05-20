from django.urls import path

from offices.views_mobile import MobileListOfficeView, MobileRetrieveOfficeView

urlpatterns = [
    path('', MobileListOfficeView.as_view()),
    path('/<uuid:pk>', MobileRetrieveOfficeView.as_view())
]

