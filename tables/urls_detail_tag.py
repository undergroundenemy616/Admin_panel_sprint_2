from django.urls import path

from tables import views

urlpatterns = [
    path('/<uuid:pk>', views.DetailTableTagView.as_view())
]
