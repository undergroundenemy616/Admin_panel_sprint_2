from tables import views
from django.urls import path

urlpatterns = [
    path('/<uuid:pk>', views.DetailTableTagView.as_view())
]
