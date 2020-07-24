import time
import jwt
from django.contrib.auth import get_user_model
from rest_framework.settings import api_settings
from users.serializers import TokenSerializer
# from rest_framework_jwt.utils import jwt_decode_handler
# from rest_framework_jwt.serializers import JSONWebTokenSerializer
# from rest_framework_jwt.authentication import JSONWebTokenAuthentication


def jwt_response_payload_handler(token, user, request):  # TODO function is not used
    """Function only for token obtain and token refresh api view. There are no need for a while."""
    return {
        'user': TokenSerializer(user, context={'request': request}).data,
        'token': token
    }


def jwt_get_secret_key(payload=None):
    """Returns user secret key or project SECRET KEY."""
    if api_settings.JWT_GET_USER_SECRET_KEY and payload is not None:
        user_model = get_user_model()  # noqa: N806
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
        api_settings.JWT_ALGORITHM
    ).decode('utf-8')


def jwt_decode_handler(token):
    """Decoded inputted jwt-token."""
    options = {
        'verify_exp': api_settings.JWT_VERIFY_EXPIRATION,
    }
    return jwt.decode(
        token,
        api_settings.JWT_PUBLIC_KEY,
        api_settings.JWT_VERIFY,
        options=options,
        leeway=api_settings.JWT_LEEWAY,
        audience=api_settings.JWT_AUDIENCE,
        issuer=api_settings.JWT_ISSUER,
        algorithms=[api_settings.JWT_ALGORITHM]
    )


def jwt_payload_handler(user):
    """Forming token payload."""
    identity = user.id
    phone_number = user.phone_number
    password = user.get_password()
    email = user.get_email()

    payload = {
        'user_id': identity,
        'phone_number': phone_number,
        'password': password,
        'email': email,
        # 'expire': time.time() + 60 * 24 * 30
    }
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = int(time.time())

    return payload
