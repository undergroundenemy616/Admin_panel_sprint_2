
from users import views
from django.urls import path

urlpatterns = [
    path('auth/', views.LoginOrRegister.as_view())
]

# urlpatterns = [
#     ...
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     ...
# ]
