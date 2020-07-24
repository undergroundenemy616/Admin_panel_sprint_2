from django.conf import settings
from django.core.cache import cache
from users.broadcasts import send_code, BaseBroadcast, SMSBroadcast
from users.models import activated_code


def register_or_initial(created: bool, user):  # register or confirm
    """In any cases the function sends an SMS to user. If the user has just been created
    or the user is re-entry..."""
    instance = SMS(user=user)

    if created is True:
        result = instance.send_code(user.last_code, refresh=False)  # Registration
        if result.get('status') is False:
            user.delete()
        return result
    else:
        return instance.send_code(user.last_code, refresh=False)  # login


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


class BroadcastAdapter(object):
    """For the full result, execution status, message,
    special data, the native broadcast interface is not suitable.
    For this, the adapter class is needed, it provides an interface
    that significantly expands the capabilities of the native one
    and provides a simple interface."""

    def __init__(self, user, broadcast):
        if not issubclass(broadcast, BaseBroadcast):
            msg = 'Expected type `{0}` got `{1}`.'.format(BaseBroadcast.__name__, broadcast.__name__)
            raise AssertionError(msg)
        if not hasattr(broadcast, 'send'):
            msg = 'Broadcast class has not method `.send()`.'
            raise AssertionError(msg)

        self.user = user  # instance of user
        self.broadcast = broadcast  # class var

    @staticmethod
    def create_result(status: bool, message: str, **kwargs) -> dict:
        """Create result when request will be done."""
        result = {'message': message, 'status': status, 'extra_data': None}
        result.update(kwargs)
        return result

    def create_broadcast(self) -> BaseBroadcast:
        """Factory method. Returns instance of broadcast."""
        return self.broadcast(client=self.user)

    def send_message(self, message: str) -> dict:
        """Base method for sending message to specify user. Returns result dict, for more
        information look at `create_result()`."""
        instance = self.create_broadcast()
        try:
            response = instance.send(message).text
        except (ValueError, KeyError, AttributeError):
            response = None

        status = instance.is_sent()
        if not status:
            return self.create_result(status, response, errors=instance.errors)
        return self.create_result(status, response)


class SMS(object):
    ERROR_EXPIRED = 'Code is expired or sms was not send!'
    ERROR_CONFIRM = 'Invalid code signature!'
    ERROR_ALREADY_SENT = 'Message already was send! Please, retry after {} seconds.'
    ERROR_INTERNAL = 'Message was not send! Internal server error.'

    MESSAGE_SENT = 'Message was send to number {}!'
    MESSAGE = 'Your activation code is: {}'

    def __init__(self, timeout=None, user=None, **kwargs):
        self.user = user
        if not self.user:
            self.phone_number = kwargs.get('phone_number', None)
        else:
            self.phone_number = user.phone_number

        self.redis_timeout = timeout or settings.KEY_EXPIRATION
        self.errors = None

    def get_value(self, phone_number=None, default=None):
        """Returns value by given phone number from `cache`."""
        if phone_number is None:
            phone_number = self.phone_number
        return cache.get(phone_number, default=default)

    def set_value(self, value, key=None, timeout=None):
        """Set to cache value by given key, if it doesn't exist key will be `phone_number`,
        Timeout is optional, that how long key will be in `cache` ."""
        if key and not isinstance(key, str):
            msg = 'Key must be string!'
            raise ValueError(msg)
        timeout = timeout or self.redis_timeout
        if key is None:
            key = self.phone_number
        return cache.set(key, value, timeout)

    def verify_code(self, code, phone_number=None):
        """Get code from `cache` and verify it with given code. Returns bool or raise."""
        cached = self.get_value(phone_number=phone_number)
        if cached is None:
            msg = self.ERROR_EXPIRED
            raise ValueError(msg)
        return cached == code

    def delete_value(self, phone_number=None):
        """Delete a key and value from `cache`. If phone_number is None - will used `self.phone_number`"""
        if phone_number is None:
            phone_number = self.phone_number
        return cache.delete(phone_number)

    def confirm_sms_code(self, sms_code, phone_number=None):
        """Gets code from Redis-cache
        by phone_number and compare it with `sms_code`."""
        if phone_number is None:
            phone_number = self.phone_number
        try:
            if self.verify_code(sms_code, phone_number=phone_number):
                self.delete_value(phone_number=phone_number)
                return True
            else:
                self.errors.append(self.ERROR_CONFIRM)
        except ValueError as error:
            self.create_errors()
            self.errors.append(error)
            return False

    def create_errors(self):
        """Just create errors list."""
        if self.errors is None:
            self.errors = list()

    def send_code(self, code=None, refresh=False) -> dict:
        """Send new activation code to user and save it to Redis and DB.
        Required `User` object in class constructor!
        The method is required for registration and authorization.
        In both cases, it checks the cache and sends a message to the user.

        Returns always a dict of results. For more, see `BroadcastAdapter.create_result()`"""

        if self.user is None:
            msg = 'User is required for sending code!'
            raise AssertionError(msg)

        broadcast = BroadcastAdapter(user=self.user, broadcast=SMSBroadcast)

        cached = self.get_value()
        if cached is not None:
            time_to_expire = cache.ttl(self.phone_number)
            return broadcast.create_result(False, 'EXCEPTION',
                                           extra_data=self.ERROR_ALREADY_SENT.format(time_to_expire))
        if refresh is True or code is None:
            code = activated_code()

        self.set_value(code)

        try:
            result = broadcast.send_message(self.MESSAGE.format(code))
            if result.get('status') is True and result.get('errors') is None:  # NO EXCEPTION, GOOD!
                self.delete_value()
        except ValueError as error:
            self.create_errors()
            self.errors.append(error)
            result = broadcast.create_result(False, 'EXCEPTION', extra_data=self.ERROR_INTERNAL)
            # self.delete_value()  # TODO test it!!
        else:
            result['extra_data'] = self.MESSAGE_SENT.format(self.phone_number)
        finally:
            self.user.last_code = code
            self.user.save()
        return result
