from datetime import datetime, timezone
from rest_framework.exceptions import ValidationError


class BookingTimeValidator:
    """
    Args:
        cls.date_to:`%YY-%MM-%DDT%HH:%MM:%SS.f`
        cls.date_from:`%YY-%MM-%DDT%HH:%MM:%SS.f`
    """
    error_message = 'Validating error'

    def __init__(self, **attrs):

        self.start = attrs.get('date_from')
        self.end = attrs.get('date_to')
        self.exc_class = attrs.get('exc_class')
        self.attrs = attrs

    def validate(self):
        self.check_datetime_instance()
        self.check_correct_period()
        self.check_future()
        return self.attrs

    def check_datetime_instance(self):
        if not isinstance((self.end or self.start), datetime):
            raise self.exc_class('')

    def check_correct_period(self):
        if self.start > self.end:
            raise self.exc_class('Ending time should be larger than the starting one')

    def check_future(self):
        current_date = datetime.utcnow().replace(tzinfo=timezone.utc)
        if self.start < current_date or self.end < current_date:
            raise self.exc_class('Cannot create booking in the past')
