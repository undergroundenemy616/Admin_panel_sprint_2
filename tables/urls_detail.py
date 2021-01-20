from django.urls import path

from tables import views

urlpatterns = [
    path('/<uuid:pk>', views.DetailTableView.as_view()),
]
