from offices import views
from django.urls import path

urlpatterns = [
    path('/<uuid:pk>', views.GroupAccessView.as_view()),
]
