from tables import views
from django.urls import path

urlpatterns = [
    path('/<uuid:pk>', views.DetailTableView.as_view()),
]
