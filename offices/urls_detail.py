from offices import views
from django.urls import path

urlpatterns = [
    path('/<uuid:pk>', views.RetrieveUpdateDeleteOfficeView.as_view())
]
