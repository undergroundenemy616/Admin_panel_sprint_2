from django.urls import path

from core.mapping import url_detail, url_list
from users import views_admin
from users.views_admin import AdminContactCheckView

urlpatterns = [
    path('/me', views_admin.AdminSelfView.as_view()),
    path('/service_email', views_admin.AdminServiceEmailView.as_view()),
    path('/pass_change', views_admin.AdminPasswordChangeView.as_view()),
    path('/pass_reset', views_admin.AdminPasswordResetView.as_view()),
    path('/promotion', views_admin.AdminPromotionDemotionView.as_view()),
    path('', views_admin.AdminUserViewSet.as_view(url_list)),
    path('/<uuid:pk>', views_admin.AdminUserViewSet.as_view(url_detail)),
    path('/validate', AdminContactCheckView.as_view())
]
