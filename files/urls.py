from django.urls import path
from files.views import ListCreateFilesView

urlpatterns = [
    path('', ListCreateFilesView.as_view())
]
