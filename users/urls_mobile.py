from django.urls import path

from users.views_mobile import (MobileAccountView, MobileEntranceCollectorView,
                                MobileLoginOrRegisterUserFromMobileView,
                                MobileRefreshTokenView,
                                MobileSingleAccountView,
                                MobileAccountMeetingSearchView)

urlpatterns = [
    path('/auth', MobileLoginOrRegisterUserFromMobileView.as_view()),
    path('/account', MobileAccountView.as_view()),
    path('/account/<uuid:pk>', MobileSingleAccountView.as_view()),
    path('/enter', MobileEntranceCollectorView.as_view()),
    path('/refresh', MobileRefreshTokenView.as_view()),
    path('/account_search', MobileAccountMeetingSearchView.as_view())
]
