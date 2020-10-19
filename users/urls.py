from users import views
from django.urls import path

urlpatterns = [
    path('auth', views.LoginOrRegisterUser.as_view()),
    path('auth/admin/login', views.LoginStaff.as_view())
]

# urlpatterns = [
#     ...
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     ...
# ]
