import uuid
from datetime import datetime, timedelta
from django.db import models
from tables.models import Table
from users.models import User
from django.db.models import Q

MINUTES_TO_ACTIVATE = 15


class BookingManager(models.Manager):
    def is_overflowed(self, table, date_from, date_to):
        """Check for booking availability"""
        overflows = self.objects(table=table, is_over=False). \
            filter(Q(date_from__gte=date_from, date_from__lte=date_to)
                   | Q(date_from__lte=date_from, date_to__gte=date_to)
                   | Q(date_from__gte=date_from, date_to__lte=date_to)
                   | Q(date_to__gt=date_from, date_to__lt=date_to))
        if overflows:
            return True
        return False


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_from = models.DateTimeField(default=datetime.utcnow)
    date_to = models.DateTimeField()
    date_activate_until = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    is_over = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, related_name="existing_bookings", null=False, on_delete=models.CASCADE)
    theme = models.CharField(default="Без темы", max_length=200)
    objects = BookingManager()

    @property
    def date_activate_until(self):
        return self.date_activate_until

    @date_activate_until.setter
    def date_activate_until(self, period: tuple):
        date_from, date_to = period
        date_now = datetime.utcnow()
        if date_now <= date_from:
            if date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):
                self.date_activate_until = date_from + timedelta(minutes=MINUTES_TO_ACTIVATE)
            else:
                self.date_activate_until = date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
        elif date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):
            self.date_activate_until = date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
        else:
            self.date_activate_until = date_to
