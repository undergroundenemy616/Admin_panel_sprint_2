from tables import views
from django.urls import path

urlpatterns = [
    path('', views.ListTables.as_view())
]
