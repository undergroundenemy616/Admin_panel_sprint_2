import jwt
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from django.utils.translation import gettext_lazy as _

from users.models import User


class AuthForAccountPut(authentication.BaseAuthentication):
    def authenticate(self, request):
        # user = get_user(request.headers['Authorization'][7:])
        payload = jwt.decode(jwt=request.headers['Authorization'][7:], verify=False)
        user = get_object_or_404(User, id=payload['user_id'])
        return user, None


def get_user(validated_token):
    """
    Attempts to find and return a user using the given validated token.
    """
    try:
        user_id = validated_token[api_settings.USER_ID_CLAIM]
    except KeyError:
        raise InvalidToken(_('Token contained no recognizable user identification'))

    try:
        user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
    except User.DoesNotExist:
        raise AuthenticationFailed(_('User not found'), code='user_not_found')

    return user
