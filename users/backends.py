import time

import jwt
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework_jwt.settings import api_settings

from users.serializers import TokenSerializer


def jwt_response_payload_handler(token, user, request):  # fixme function is not used
    """Function only for token obtain and token refresh api view. There are no need for a while."""
    return {
        'user': TokenSerializer(user, context={'request': request}).data,
        'token': token
    }


def jwt_get_secret_key(payload=None):
    """Returns user secret key or project SECRET KEY."""
    if api_settings.JWT_GET_USER_SECRET_KEY and payload is not None:
        user_model = get_user_model()
        if not hasattr(user_model, 'objects'):
            msg = 'Default user model has not attribute `objects`.'
            raise AssertionError(msg)
        user = user_model.objects.get(pk=payload.get('user_id'))
        key = str(api_settings.JWT_GET_USER_SECRET_KEY(user))
        return key
    return api_settings.JWT_SECRET_KEY


def jwt_encode_handler(payload):
    """Function encode inputted payload with secret key. Returns decoded jwt-string."""
    key = api_settings.JWT_PRIVATE_KEY or jwt_get_secret_key(payload)
    return jwt.encode(
        payload,
        key,
        api_settings.JWT_ALGORITHM,
        json_encoder=DjangoJSONEncoder
    ).decode('utf-8')


def jwt_decode_handler(token):
    """Decoded inputted jwt-token."""
    options = {
        'verify_exp': api_settings.JWT_VERIFY_EXPIRATION,
    }
    secret_key = jwt_get_secret_key()

    return jwt.decode(
        token,
        api_settings.JWT_PUBLIC_KEY or secret_key,
        api_settings.JWT_VERIFY,
        options=options,
        leeway=api_settings.JWT_LEEWAY,
        audience=api_settings.JWT_AUDIENCE,
        issuer=api_settings.JWT_ISSUER,
        algorithms=[api_settings.JWT_ALGORITHM]
    )


def jwt_payload_handler(user):
    """Forming token payload."""
    payload = {'user_id': user.id}

    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = int(time.time())

    return payload


def jwt_get_username_from_payload(payload):
    """Get user `phone_number` for authorization instead of `username`."""
    return payload.get('user_id')

