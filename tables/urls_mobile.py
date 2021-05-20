from django.urls import include, path

from tables.views_mobile import MobileTableSlotsView, MobileTableTagView, MobileTableViewSet

urlpatterns = [
    path('/<uuid:pk>', MobileTableViewSet.as_view({'get': 'retrieve'})),
    path('/table_slot/<uuid:pk>', MobileTableSlotsView.as_view()),
    path('/table_tag', MobileTableTagView.as_view())
]
