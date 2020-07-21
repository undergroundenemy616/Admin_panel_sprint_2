from django.conf import settings
from django.core.cache import cache
from users.backends import SMSBroadcast
from users.models import activated_code


def send_code(message, to_user):
    """Send message and return instance of SMSBroadcast"""
    sms = SMSBroadcast(client=to_user)
    sms.send(message)
    return sms


def sending_response(message: str, status: str) -> dict:
    """Create and return response of registration or login."""
    response = dict()
    response['message'] = message
    response['status'] = status.upper()
    return response


def register_or_send_sms(user, created):
    """Register or login user."""
    if created is True:
        register(user)  # Registration
    else:
        send_new_code(user)  # Login


def register(user) -> dict:
    """Register new user."""
    last_code = user.last_code
    cache.set(user.phone_number, last_code, timeout=settings.KEY_EXPIRATION)

    message = 'Your activation code is: {}'.format(last_code)
    sms = send_code(message, user)

    if not sms.is_sent():
        response_msg = 'Message was not send! User will be deleted.'
        cache.delete(user.phone_number)
        user.delete()
        return sending_response(response_msg, 'error')

    response_msg = 'Message was send to number {}!'.format(user.phone_number)
    return sending_response(response_msg, status='done')


def send_new_code(user) -> dict:
    """Send new activation code to user and save it to Redis and DB."""
    cached = cache.get(user.phone_number)
    if cached is not None:
        time_to_expire = cache.ttl(user.phone_number)
        response_msg = 'SMS-code already was send! Please, retry after {} sec'.format(time_to_expire)
        return sending_response(response_msg, 'error')

    new_code = activated_code()
    cache.set(user.phone_number, new_code, timeout=settings.KEY_EXPIRATION)
    user.last_code = new_code
    user.save()

    message = 'Your activation code is: {}'.format(new_code)
    sms = send_code(message, user)

    if not sms.is_sent():
        cache.delete(user.phone_number)
        response_msg = 'Message was not send! Internal server error.'
        return sending_response(response_msg, 'error')
    response_msg = 'Message was send to number {}!'.format(user.phone_number)
    return sending_response(response_msg, 'done')


def confirm_sms_code(sms_code, user):
    """Confirm inputted sms code."""
    cached = cache.get(user.phone_number)
    if not cached:
        msg = 'Code is expired or sms was not send!'
        raise ValueError(msg)
    if cached != sms_code:
        msg = 'Invalid sms code!'
        raise ValueError(msg)

    try:
        pass
        # token = tokenized(user)  # TODO
        # response = {'user': user, 'account': account, 'auth': token}
        # return Response()
    finally:
        cache.delete(user.phone_number)
