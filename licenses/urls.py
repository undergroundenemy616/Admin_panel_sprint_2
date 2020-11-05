from licenses import views
from django.urls import path

urlpatterns = [
    path('', views.ListLicensesView.as_view()),
]
