from django.urls import path

from groups import views

urlpatterns = [
    path('/<uuid:pk>', views.DetailGroupView.as_view())
]
