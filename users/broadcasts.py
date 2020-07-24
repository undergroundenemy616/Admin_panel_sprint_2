import urllib.parse
import requests
from abc import ABC, abstractmethod
from django.conf import settings
from users.models import User


def send_code(message, phone_number):
    """Util for sending message and returning instance of SMSBroadcast.
    Returns sms-instance and text of the response."""
    sms = SMSBroadcast(phone_number=phone_number)
    response = sms.send(message).text
    return sms, response


class AbstractBroadcast(ABC):
    @abstractmethod
    def send(self, *args, **kwargs):
        """Method must be implemented"""
        pass

    @abstractmethod
    def is_sent(self):
        """Method must be implemented"""
        pass


class BaseBroadcast(AbstractBroadcast):
    """Strategy pattern."""
    TIMEOUT = 3

    def __init__(self, client=None, method='GET'):
        self.client = client
        self.errors = None
        self.method = method or 'POST'

        self.response = None

        self.validate()

    def validate(self):
        """If you need to validate any variable, you can
        override this hook and call methods from here."""
        if not isinstance(self.method, str):
            msg = 'Method must instance of string and contains `POST`, `GET`, etc requests.'
            raise AssertionError(msg)

    @staticmethod
    def validate_message(msg):
        """Validate message before sending"""
        if not msg:
            error_msg = 'Message can not be None!'
            raise ValueError(error_msg)
        return msg

    @staticmethod
    def validate_recipient(recipient):
        """Validate destination address before sending"""
        if not recipient:
            error_msg = 'Destination is None!'
            raise ValueError(error_msg)
        return recipient

    @staticmethod
    def encode_url(params: dict) -> str:  # FIXME will be deleted
        """Encode params to url-string."""
        return urllib.parse.urlencode(params)

    def is_sent(self):
        """Returns flag is message was send."""
        return not bool(self.errors)

    def send(self, recipient, body=None, **kwargs):
        """Returns boolean. False if sms was not be send, else True.
        `recipient` is full link to service, example: 'https://smsc.com/send'.

        For sending query params, use keyword argument `params={}`.
        """
        self.errors = list()

        recipient = self.validate_recipient(recipient)
        if body is None and self.method == 'POST':
            body = {}

        try:
            self.response = self._send(recipient, body, **kwargs)
        except Exception as error:
            self.errors.append(error)
            return None

        return self.response

    def _send(self, recipient, body, **kwargs):
        if self.method == 'POST':
            response = requests.post(recipient, data=body,
                                     timeout=self.TIMEOUT, params=kwargs)
        else:
            response = requests.get(recipient, timeout=self.TIMEOUT, params=kwargs)
        return response


class SMSBroadcast(BaseBroadcast):
    def __init__(self, url=None, login=None,
                 password=None, extra_params=None,
                 charset=None, phone_number=None, *args, **kwargs):
        client = kwargs.get('client')

        if not phone_number and not client:
            msg = 'No recipient to send a message!'
            raise AssertionError(msg)

        self.phone_number = self.get_phone_number(phone_number, client)

        self.url = url or settings.SMSC['SMSC_SEND_URL']  # TODO change it to application settings
        self.login = login or settings.SMSC['SMSC_LOGIN']
        self.password = password or settings.SMSC['SMSC_PASSWORD']
        self.charset = charset or settings.SMSC['SMSC_CHARSET']

        self.params = extra_params
        super(SMSBroadcast, self).__init__(*args, **kwargs)

    def get_phone_number(self, phone_number, client):
        """Method returns phone_number."""
        if phone_number:
            phone_number = str(phone_number)
            return User.normalize_phone(phone_number)
        else:
            self.check_recipient(client)
            return client.phone_number

    @staticmethod
    def check_recipient(client):
        """Check client fields."""
        if not hasattr(client, 'phone_number'):
            msg = 'User has not field `phone_number`'
            raise AssertionError(msg)

    def send(self, message, **kwargs):
        """Send SMS message to one client."""
        kwargs.pop('theme', None)
        params = self.create_params(message=message)
        if params:
            params.update(kwargs)
        url_for_send = self.url
        return super(SMSBroadcast, self).send(url_for_send, **params)

    def create_params(self, message: str) -> dict:
        """Create query parameters for url."""
        params = {'login': self.login, 'psw': self.password, 'phones': self.phone_number, 'mes': message}
        if self.params:
            params.update(self.params)
        return params

# TODO add docs
# TODO add tests
