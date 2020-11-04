import uuid
from datetime import datetime, timedelta, timezone
from django.db import models

from booking_api_django_new.settings import BOOKING_PUSH_NOTIFY_UNTIL_MINS
from core.scheduler import scheduler
from push_tokens.send_interface import send_push_message
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
        self.create_oncoming_notification()
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

    def notify_about_oncoming_booking(self):
        """Send PUSH-notification about oncoming booking to every user devices"""
        if not self.is_over \
                and (self.date_from - datetime.now()).total_seconds() / 60.0 <= BOOKING_PUSH_NOTIFY_UNTIL_MINS + 5 \
                and self.user.account and self.user.account.push_tokens.all():
            expo_data = {
                "title": "Уведомление о предстоящем бронировании",
                "body": f"Ваше бронирование начнется через 15 минут. Не забудьте подтвердить.",
                "data": {
                    "go_booking": True
                }
            }
            for token in [push_object.token for push_object in self.user.account.push_tokens.all()]:
                send_push_message(token, expo_data)

    def create_oncoming_notification(self):
        """Add job in apscheduler to notify user about oncoming booking via PUSH-notification"""
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        if (self.date_from - date_now).total_seconds() / 60.0 > BOOKING_PUSH_NOTIFY_UNTIL_MINS:
            scheduler.add_job(
                self.notify_about_oncoming_booking,
                "date",
                run_date=self.date_from - timedelta(minutes=BOOKING_PUSH_NOTIFY_UNTIL_MINS),
                # args=[self],
                misfire_grace_time=900,
                id="notify_about_oncoming_booking_" + str(self.id)
            )
