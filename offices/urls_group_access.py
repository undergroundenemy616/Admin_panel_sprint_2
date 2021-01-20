from django.urls import path

from offices import views

urlpatterns = [
    path('/<uuid:pk>', views.GroupAccessView.as_view()),
]
