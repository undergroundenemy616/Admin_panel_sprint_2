from django.conf import settings
from django.core.cache import cache
from users.broadcasts import send_code, BaseBroadcast
from users.models import activated_code


def register_or_send_sms(created: bool, user):
    """Register or login user. It is initial login."""
    if created is True:
        return register(user)  # Registration
    else:
        return send_new_code(user)  # Login


class BroadcastAdapter(object):
    """Adapter"""

    def __init__(self, user, broadcast):
        if not isinstance(broadcast, BaseBroadcast):
            msg = 'Expected type `{0}` got `{1}`.'.format(BaseBroadcast.__name__, broadcast.__name__)
            raise AssertionError(msg)
        if not hasattr(broadcast, 'send'):
            msg = 'Broadcast class has not method `.send()`.'
            raise AssertionError(msg)

        self.user = user
        self.broadcast = broadcast  # class var

    def send_message(self, message):
        """Method send message to specify user by broadcast interface."""


def confirm_sms_code(sms_code, phone_number):
    """Gets code from Redis-cache
    by phone_number and compare it with `sms_code`."""
    cached = cache.get(phone_number)
    if not cached:
        msg = 'Code is expired or sms was not send!'
        return False, msg
    if cached != sms_code:
        msg = 'Invalid sms code!'
        return False, msg

    cache.delete(phone_number)
    return True


def create_result(status: bool, message: str) -> dict:
    """Create and return response of registration or login."""
    return {'message': message, 'status': status}


def register(user) -> (dict, int):
    """Register new user."""
    last_code = user.last_code
    cache.set(user.phone_number, last_code, timeout=settings.KEY_EXPIRATION)

    message = 'Your activation code is: {}'.format(last_code)
    sms = send_code(message, user.phone_number)

    if not sms.is_sent():
        msg = 'Message was not send! User will be deleted.'
        cache.delete(user.phone_number)
        user.delete()
        return False, msg

    response_msg = 'Message was send to number: {}!'.format(user.phone_number)
    return True, response_msg


def send_new_code(user) -> (dict, int):
    """Send new activation code to user and save it to Redis and DB."""
    cached = cache.get(user.phone_number)
    if cached is not None:
        time_to_expire = cache.ttl(user.phone_number)
        msg = 'Message already was send! Please, retry after {} sec'.format(time_to_expire)
        return False, msg

    new_code = activated_code()
    cache.set(user.phone_number, new_code, timeout=settings.KEY_EXPIRATION)
    user.last_code = new_code
    user.save()

    message = 'Your activation code is: {}'.format(new_code)
    sms = send_code(message, user.phone_number)

    if not sms.is_sent():
        cache.delete(user.phone_number)
        msg = 'Message was not send! Internal server error.'
        return False, msg
    response_msg = 'Message was send to number {}!'.format(user.phone_number)
    return True, response_msg
