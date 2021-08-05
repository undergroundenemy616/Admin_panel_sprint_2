from django.urls import path

from users.views_mobile import (MobileAccountView, MobileEntranceCollectorView,
                                MobileLoginOrRegisterUserFromMobileView,
                                MobileRefreshTokenView,
                                MobileUserRegisterView, MobilePasswordChangeView,
                                MobilePasswordResetView, MobileUserLoginView,
                                MobileSingleAccountView,
                                MobileAccountMeetingSearchView, MobileSelfView,
                                MobileConformationView, MobileContactCheckView,
                                MobileCheckAvailableView)

urlpatterns = [
    path('/auth', MobileLoginOrRegisterUserFromMobileView.as_view()),
    path('/account', MobileAccountView.as_view()),
    path('/account/<uuid:pk>', MobileSingleAccountView.as_view()),
    path('/enter', MobileEntranceCollectorView.as_view()),
    path('/refresh', MobileRefreshTokenView.as_view()),
    path('/login', MobileUserLoginView.as_view()),
    path('/registration', MobileUserRegisterView.as_view()),
    path('/change_password', MobilePasswordChangeView.as_view()),
    path('/pass_reset', MobilePasswordResetView.as_view()),
    path('/confirm', MobileConformationView.as_view()),
    path('/account_search', MobileAccountMeetingSearchView.as_view()),
    path('/check_available', MobileCheckAvailableView.as_view()),
    path('/me', MobileSelfView.as_view()),
    path('/validate', MobileContactCheckView.as_view())
]
