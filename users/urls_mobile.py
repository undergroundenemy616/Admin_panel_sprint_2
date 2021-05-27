from django.urls import path

from users.views_mobile import (MobileAccountView, MobileEntranceCollectorView,
                                MobileLoginOrRegisterUserFromMobileView,
                                MobileRefreshTokenView,
                                MobileSingleAccountView)

urlpatterns = [
    path('/auth', MobileLoginOrRegisterUserFromMobileView.as_view()),
    path('/account', MobileAccountView.as_view()),
    path('/account/<uuid:pk>', MobileSingleAccountView.as_view()),
    path('/enter', MobileEntranceCollectorView.as_view()),
    path('/refresh', MobileRefreshTokenView.as_view()),
]
