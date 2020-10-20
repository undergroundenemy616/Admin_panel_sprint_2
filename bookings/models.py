import uuid
from datetime import datetime, timedelta, timezone
from django.db import models
from tables.models import Table
from users.models import User
from django.db.models import Q

MINUTES_TO_ACTIVATE = 15


class BookingManager(models.Manager):
    def is_overflowed(self, table, date_from, date_to):
        """Check for booking availability"""
        overflows = self.model.objects.filter(table=table, is_over=False). \
            filter(Q(date_from__gte=date_from, date_from__lte=date_to)
                   | Q(date_from__lte=date_from, date_to__gte=date_to)
                   | Q(date_from__gte=date_from, date_to__lte=date_to)
                   | Q(date_to__gt=date_from, date_to__lt=date_to))
        if overflows:
            return True
        return False

    def create(self, **kwargs):
        """Check for consecutive bookings and merge instead of create if exists"""
        obj = self.model(**kwargs)
        consecutive_booking = obj.get_consecutive_booking()
        if consecutive_booking:
            consecutive_booking.date_to = obj.date_to
            consecutive_booking.save()
            return consecutive_booking
        else:
            obj.save()
            return obj

    def active_only(self):
        return self.get_queryset().filter(is_active=True)


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_from = models.DateTimeField(default=datetime.utcnow)
    date_to = models.DateTimeField()
    date_activate_until = models.DateTimeField(null=True)
    # TODO: Why it is not a property ?
    is_active = models.BooleanField(default=False)
    is_over = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, related_name="existing_bookings", null=False, on_delete=models.CASCADE)
    theme = models.CharField(default="Без темы", max_length=200)
    objects = BookingManager()

    def save(self, *args, **kwargs):
        self.date_activate_until = self.calculate_date_activate_until()
        super(self.__class__, self).save(*args, **kwargs)

    def get_consecutive_booking(self):
        """Returns previous booking if exists for merging purpose"""
        try:
            return Booking.objects.get(
                user=self.user,
                table=self.table,
                theme=self.theme,
                date_to=self.date_from,
                is_over=False
            )
        except (Booking.MultipleObjectsReturned, Booking.DoesNotExist):
            return None

    def calculate_date_activate_until(self):
        """Calculation of activation date depending on current time"""
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        if date_now <= self.date_from:  # noqa
            if self.date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):  # noqa
                return self.date_from + timedelta(minutes=MINUTES_TO_ACTIVATE)  # noqa
            else:
                return date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
        elif self.date_to >= date_now + timedelta(minutes=MINUTES_TO_ACTIVATE):  # noqa
            return date_now + timedelta(minutes=MINUTES_TO_ACTIVATE)
        else:
            return self.date_to
