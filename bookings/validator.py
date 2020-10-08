from datetime import datetime
from rest_framework.exceptions import ValidationError


class BookingTimeValidator:
    """
    Args:
        cls.date_to:`%YY-%MM-%DDT%HH:%MM:%SS.f`
        cls.date_from:`%YY-%MM-%DDT%HH:%MM:%SS.f`
    """
    error_message = 'Validating error'

    def __init__(self, date_to, date_from, exc_class=None):

        self.start = date_from
        self.end = date_to
        self.exc_class = exc_class
        self.error = []

    @property
    def is_valid(self):
        return not bool(self.error)

    def validate(self):
        try:
            self.check_datetime_instance()
            self.check_correct_period()
            self.check_future()
        except Exception as error:
            self.error.append(error)

    def check_datetime_instance(self):
        if not isinstance((self.end or self.start), datetime):
            raise self.exc_class('')

    def check_correct_period(self):
        if self.start > self.end:
            raise self.exc_class('Ending time should be larger than the starting one')

    def check_future(self):
        if self.start < datetime.utcnow() or self.end < datetime.utcnow():
            raise self.exc_class('Cannot create booking in the past')

    def check_activation_date(self):
        pass

    def check_multi(self):
        minutes = (00, 15, 30, 45)
        for t in (self.start, self.end):
            if t.minute not in minutes:
                msg = 'You can only reserve a time that is a multiple of 30 minutes'
                raise self.exc_class(msg)


