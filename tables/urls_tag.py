from tables import views
from django.urls import path

urlpatterns = [
    path('', views.TableTagView.as_view())
]
