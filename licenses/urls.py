from django.urls import path

from licenses import views

urlpatterns = [
    path('', views.ListLicensesView.as_view()),
]
