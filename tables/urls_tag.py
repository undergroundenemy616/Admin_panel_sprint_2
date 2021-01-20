from django.urls import path

from tables import views

urlpatterns = [
    path('', views.TableTagView.as_view())
]
