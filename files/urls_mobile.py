from django.urls import path

from files.views_mobile import MobileListCreateFilesView

urlpatterns = [
    path('', MobileListCreateFilesView.as_view())
]
