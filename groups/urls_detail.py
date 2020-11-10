from groups import views
from django.urls import path

urlpatterns = [
    path('/<uuid:pk>', views.DetailGroupView.as_view())
]
