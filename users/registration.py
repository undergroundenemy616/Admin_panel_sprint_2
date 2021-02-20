from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from users.broadcasts import SMSBroadcast
from users.models import activated_code


def send_code(user, is_created):
    code = activated_code()
    redis = UserRedisWrapper(user.phone_number)

    print("Code is:", code)

    # Check key in redis, if it already exists - raise exception.
    ttl = redis.get_ttl()
    if ttl:
        raise ValidationError(detail={"detail": f'Message already sent! Please, retry after {ttl}',
                                      "time": ttl}, code=400)

    # Send created code to user's phone.
    broadcast = SMSBroadcast(phone_number=user.phone_number)
    message = f'Your activation code is: {code}'
    broadcast.send(message=message)  # TODO create celery

    # If something went wrong, user will be deleted and anyway raised exception.
    if not broadcast.is_sent:
        if is_created:
            user.delete()
        raise ValueError('Message was not send!')

    # Cache code to redis for 3 minutes
    # import django_redis
    redis.set_value(code)

    # At least we save code to user field
    user.last_code = code
    user.save()


def confirm_code(phone_number, code):
    redis = UserRedisWrapper(phone_number)
    redis.check_exists()
    redis.verify_code(code)
    redis.delete_value()


class RedisWrapper:
    def __init__(self, key):
        self.key = key
        self.timeout = settings.KEY_EXPIRATION
        self.validate_init()

    def validate_init(self):
        """Validating `self.key`."""
        if not isinstance(self.key, str):
            msg = f'Phone number must be str, got {type(self.key)}'
            raise TypeError(msg)

    def get_value(self, default=None):
        """Get value from redis cache."""
        return cache.get(self.key, default=default)

    def set_value(self, value):
        """Set value to redis cache."""
        return cache.set(self.key, value, self.timeout)

    def is_exists(self):
        """Returns flag is key exists."""
        return cache.has_key(self.key)

    def delete_value(self):
        """Delete key and value from redis."""
        return cache.delete(self.key)

    def get_ttl(self):
        """Get ttl, time-to-live, if key doesn't exist, returns None."""
        return cache.ttl(self.key)

    def check_exists(self):
        """Checking, if key is not exists raise an error."""
        cached = self.get_value()
        if not cached:
            raise ValueError('Key does not exist or timed out!')


class UserRedisWrapper(RedisWrapper):
    def verify_code(self, code):
        """Verified given code with existing."""
        cached = self.get_value()
        if cached != code:
            raise ValueError('Invalid sms-code!')
