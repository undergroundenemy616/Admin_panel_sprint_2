import logging
from abc import ABC, abstractmethod

import requests
from django.conf import settings

from users.models import User


class AbstractBroadcast(ABC):
    @abstractmethod
    def send(self, *args, **kwargs):
        """Method must be implemented"""


class BaseBroadcast(AbstractBroadcast):
    """Strategy pattern."""
    TIMEOUT = 3

    def __init__(self):
        self.errors = list()
        self.logger = logging.getLogger('__name__')

    @property
    def is_sent(self):
        """Returns flag True if message was send."""
        return not bool(self.errors)

    def send(self, url=None, data=None, **params):
        """Builder method"""
        url = self.build_url(url)
        data = self.build_data(data)
        extra = self.build_params(**params)
        try:
            response = self._send(url, data, extra)
            self.validate(response)
        except Exception as error:
            self.logger.exception(error)
            self.errors.append(error)
        else:
            return response

    def _send(self, url, body, extra):
        """Send request."""
        response = requests.post(url=url, data=body, timeout=self.TIMEOUT, params=extra)
        return response

    def build_url(self, *args, **kwargs):
        """Method must be override."""

    def build_data(self, *args, **kwargs):
        """Method must be override."""

    def build_params(self, *args, **kwargs):
        """Method must be override."""

    def validate(self, *args, **kwargs):
        """Validating hook."""


class SMSBroadcast(BaseBroadcast):
    def __init__(self, phone_number):
        self.phone_number = self.normalize_phone(phone_number)

        self.url = settings.SMSC['SMSC_SEND_URL']
        self.login = settings.SMSC['SMSC_LOGIN']
        self.password = settings.SMSC['SMSC_PASSWORD']

        super(SMSBroadcast, self).__init__()

    @staticmethod
    def normalize_phone(phone_number):
        return User.normalize_phone(phone_number)

    def build_url(self, *args, **kwargs):
        """Returns `self.url` from django settings"""
        return self.url

    def build_data(self, *args, **kwargs):
        """Signature complete"""

    def build_params(self, message):
        """Create query string params for url"""
        extra = {'login': self.login, 'psw': self.password, 'phones': self.phone_number, 'mes': message}
        return extra

    def validate(self, response):
        """Validating response."""
        if 'OK' not in response.text:
            raise ValueError('Invalid response from server!')
