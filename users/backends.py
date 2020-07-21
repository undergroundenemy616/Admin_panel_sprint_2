from abc import ABC, abstractmethod


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
    def __init__(self, client=None):
        self.client = client
        self.errors = None

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

    def is_sent(self):
        """Returns flag is message was send."""
        return not bool(self.errors)

    def send(self, message, recipient, *args, **kwargs):
        """Returns boolean. False if sms was not be send, else True."""
        self.errors = list()

        message = self.validate_message(message)
        recipient = self.validate_recipient(recipient)

        try:
            self._send(message, recipient, *args, **kwargs)
        except Exception as error:
            self.errors.append(error)

    def _send(self, message, recipient, *args, **kwargs):
        # logic about send
        pass


class SMSBroadcast(BaseBroadcast):
    def check_user(self):
        """Check client fields."""
        if not hasattr(self.client, 'phone_number'):
            msg = 'User has not field `phone_number`'
            raise AssertionError(msg)

    def send(self, message, *args, **kwargs):
        """Send SMS message to `self.client.phone_number`!"""
        kwargs.pop('theme')

        self.check_user()
        recipient = self.client.phone_number
        return super(SMSBroadcast, self).send(message, recipient, *args, **kwargs)
