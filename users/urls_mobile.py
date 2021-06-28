from django.urls import path

from users.views_mobile import (MobileAccountView, MobileEntranceCollectorView,
                                MobileLoginOrRegisterUserFromMobileView,
                                MobileRefreshTokenView,
                                MobileUserRegisterView, MobilePasswordChangeView,
                                MobilePasswordResetView, MobileUserLoginView, MobileEmailConformationView,
                                MobilePhoneConformationView,
                                MobileSingleAccountView,
                                MobileAccountMeetingSearchView, MobileSelfView)

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
    path('/confirm_email', MobileEmailConformationView.as_view()),
    path('/confirm_phone', MobilePhoneConformationView.as_view()),
    path('/account_search', MobileAccountMeetingSearchView.as_view()),
    path('/me', MobileSelfView.as_view()),
]
