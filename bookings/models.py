import os
import uuid

from rest_framework import status

from booking_api_django_new.celery import app as celery_app
from celery.app.control import Control
import bookings.tasks as tasks
from datetime import datetime, timedelta, timezone

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Min, Q
from django.utils.timezone import now

from booking_api_django_new.settings import (BOOKING_PUSH_NOTIFY_UNTIL_MINS,
                                             BOOKING_TIMEDELTA_CHECK,
                                             PUSH_HOST)
from core.handlers import ResponseException
from group_bookings.models import GroupBooking

from groups.models import EMPLOYEE_ACCESS
from offices.models import Office
from push_tokens.send_interface import send_push_message
from tables.models import Table
from users.models import Account, User

MINUTES_TO_ACTIVATE = 15


class BookingManager(models.Manager):
    def is_overflowed(self, table, date_from, date_to):
        """Check for booking availability"""
        overflows = self.model.objects.filter(table=table, is_over=False, status__in=['waiting', 'active']). \
            filter((Q(date_from__lt=date_to, date_to__gte=date_to)
                    | Q(date_from__lte=date_from, date_to__gt=date_from)
                    | Q(date_from__gte=date_from, date_to__lte=date_to)) & Q(
            date_from__lt=date_to))  # | Q(date_to__gt=date_from, date_to__lt=date_to)
        if overflows:
            return True
        return False

    def is_overflowed_with_data(self, table, date_from, date_to):
        """Check for booking availability"""
        overflows = self.model.objects.filter(table=table, is_over=False, status__in=['waiting', 'active']). \
            filter((Q(date_from__lt=date_to, date_to__gte=date_to)
                    | Q(date_from__lte=date_from, date_to__gt=date_from)
                    | Q(date_from__gte=date_from, date_to__lte=date_to)) & Q(date_from__lt=date_to)).select_related(
            'table')
        # Q(date_from__gt=date_from, date_from__lt=date_to)
        # | Q(date_from__lt=date_from, date_to__gt=date_to)
        # | Q(date_from__gt=date_from, date_to__lt=date_to)
        # | Q(date_to__gt=date_from, date_to__lt=date_to)
        if overflows:
            return overflows
        return []

    def is_user_overflowed(self, account, room_type, date_from, date_to):
        try:
            access = account.groups.aggregate(Min('access')) if account.groups.exists() else {'access__min': EMPLOYEE_ACCESS}
        except AttributeError:
            access = {'access__min': EMPLOYEE_ACCESS}
        if access['access__min'] < EMPLOYEE_ACCESS:
            return False
        overflows = self.model.objects.filter(user=account, table__room__type__unified=room_type, is_over=False,
                                              status__in=['waiting', 'active']). \
            filter((Q(date_from__lt=date_to, date_to__gte=date_to)
                    | Q(date_from__lte=date_from, date_to__gt=date_from)
                    | Q(date_from__gte=date_from, date_to__lte=date_to)) & Q(date_from__lt=date_to))
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
    STATUS = (
        ('waiting', 'waiting'),
        ('active', 'active'),
        ('canceled', 'canceled'),
        ('auto_canceled', 'auto_canceled'),
        ('over', 'over')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_from = models.DateTimeField(default=datetime.utcnow)
    date_to = models.DateTimeField()
    date_activate_until = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=False)
    is_over = models.BooleanField(default=False)
    user = models.ForeignKey(Account, null=False, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, related_name="existing_bookings", null=False, on_delete=models.CASCADE)
    theme = models.CharField(default="Без темы", max_length=200)
    status = models.CharField(choices=STATUS, null=False, max_length=20, default='waiting')
    group_booking = models.ForeignKey(GroupBooking, on_delete=models.CASCADE,
                                      null=True, default=None, related_name='bookings')
    objects = BookingManager()

    def save(self, *args, **kwargs):
        office = Office.objects.get(id=self.table.room.floor.office_id)
        open_time, close_time = office.working_hours.split('-')
        open_time = datetime.strptime(open_time, '%H:%M')
        close_time = datetime.strptime(close_time, '%H:%M')
        if not open_time.time() <= self.date_from.time() <= close_time.time() and not \
                open_time.time() <= self.date_to.time() <= close_time.time():
            raise ResponseException('The selected time does not fall into the office work schedule',
                                    status_code=status.HTTP_400_BAD_REQUEST)
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.date_activate_until = self.calculate_date_activate_until()
        if not JobStore.objects.filter(job_id__contains=str(self.id)):
            JobStore.objects.create(job_id='check_booking_activate_'+str(self.id),
                                    time_execute=self.date_activate_until,
                                    parameters={'uuid': str(self.id)})
            JobStore.objects.create(job_id='make_booking_over_'+str(self.id),
                                    time_execute=self.date_to,
                                    parameters={'uuid': str(self.id)})
            if date_now + timedelta(minutes=BOOKING_TIMEDELTA_CHECK) > self.date_from:
                JobStore.objects.create(job_id='notify_about_booking_activation_'+str(self.id),
                                        time_execute=date_now + timedelta(minutes=1),
                                        parameters={'uuid': str(self.id)})
                tasks.notify_about_booking_activation.apply_async(
                    args=[self.id],
                    eta=date_now + timedelta(minutes=1),
                    task_id='notify_about_activation_booking_' + str(self.id))
            else:
                JobStore.objects.create(job_id='notify_about_booking_activation_' + str(self.id),
                                        time_execute=self.date_from - timedelta(minutes=BOOKING_TIMEDELTA_CHECK),
                                        parameters={'uuid': str(self.id)})
            if date_now + timedelta(minutes=BOOKING_PUSH_NOTIFY_UNTIL_MINS) < self.date_from:
                JobStore.objects.create(job_id='notify_about_oncoming_booking_'+str(self.id),
                                        time_execute=self.date_from - timedelta(minutes=BOOKING_PUSH_NOTIFY_UNTIL_MINS),
                                        parameters={'uuid': str(self.id)})

        super(self.__class__, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.set_booking_over()
        super(self.__class__, self).delete(using, keep_parents)

    def set_booking_active(self, *args, **kwargs):
        try:
            instance = Booking.objects.get(id=self.id)
        except ObjectDoesNotExist:
            return
        instance.is_active = True
        instance.is_over = False
        instance.status = 'active'
        instance.table.set_table_occupied()
        super(Booking, instance).save(*args, **kwargs)

    def set_booking_over(self, *args, **kwargs):
        try:
            instance = Booking.objects.get(id=self.id)
        except ObjectDoesNotExist:
            return
        instance.is_active = False
        instance.is_over = True
        if kwargs.get('kwargs'):
            if kwargs['kwargs'].get('status') != 'auto_over':
                instance.date_to = now()
            else:
                instance.status = 'auto_over'
            if kwargs['kwargs'].get('status') == 'auto_canceled':
                instance.status = 'auto_canceled'
            elif kwargs['kwargs'].get('status') == 'over':
                instance.status = 'over'
        else:
            instance.date_to = now()
            instance.status = 'canceled'
        instance.table.set_table_free()

        control = Control(app=celery_app)
        if kwargs.get('kwargs'):
            if kwargs['kwargs'].get('source') == 'check_activate':
                control.revoke(task_id='make_booking_over_' + str(self.id))
                control.revoke(task_id='notify_about_oncoming_booking_' + str(self.id))
                control.revoke(task_id='notify_about_activation_booking_' + str(self.id))
            else:
                control.revoke(task_id='check_booking_activate_' + str(self.id))
                control.revoke(task_id='make_booking_over_' + str(self.id))
                control.revoke(task_id='notify_about_oncoming_booking_' + str(self.id))
                control.revoke(task_id='notify_about_activation_booking_' + str(self.id))

        super(Booking, instance).save()

    def check_booking_activate(self, *args, **kwargs):
        try:
            instance = Booking.objects.get(id=self.id)
        except ObjectDoesNotExist:
            return
        if not instance.is_active:
            flag = {'status': 'auto_canceled'}
            instance.set_booking_over(kwargs=flag)

    def make_booking_over(self, *args, **kwargs):
        try:
            instance = Booking.objects.get(id=self.id)
        except ObjectDoesNotExist:
            return
        flag = {'status': 'over'}
        instance.set_booking_over(kwargs=flag)

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
        #  and (self.date_from - datetime.now()).total_seconds() / 60.0 <= BOOKING_PUSH_NOTIFY_UNTIL_MINS + 5 \
        push_group = os.environ.get("PUSH_GROUP")
        if push_group and not self.is_over \
                and self.user:
            expo_data = {
                "account": str(self.user.id),
                "app": push_group,
                "expo": {
                    "title": "Уведомление о предстоящем бронировании",
                    "body": f"Ваше бронирование начнется меньше чем через час. Не забудьте отсканировать QR-код для подтверждения.",
                    "data": {
                        "go_booking": True
                    }
                }
            }
            response = requests.post(
                PUSH_HOST + "/send_push",
                json=expo_data,
                headers={'content-type': 'application/json'}
                # auth=(FILES_USERNAME, FILES_PASSWORD),
            )
            if response.status_code != 200:
                print(f"Unable to send push message for {str(self.user.id)}: {response.json().get('message')}")

    def notify_about_booking_activation(self):
        """Send PUSH-notification about opening activation"""
        #  and (self.date_from - datetime.now()).total_seconds() / 60.0 <= BOOKING_TIMEDELTA_CHECK \
        push_group = os.environ.get("PUSH_GROUP")
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        if push_group and not self.is_over \
                and self.user:
            expo_data = {
                "account": str(self.user.id),
                "app": push_group,
                "expo": {
                    "title": "Открыто подтверждение!",
                    "body": "Вы можете подтвердить бронирование QR-кодом в течение 30 минут.",
                    "data": {
                        "go_booking": True
                    }
                }
            }
            response = requests.post(
                PUSH_HOST + "/send_push",
                json=expo_data,
                headers={'content-type': 'application/json'}
                # auth=(FILES_USERNAME, FILES_PASSWORD),
            )
            if response.status_code != 200:
                print(f"Unable to send push message for {str(self.user.id)}: {response.json().get('message')}")
            # for token in [push_object.token for push_object in self.user.push_tokens.all()]:
            #     send_push_message(token, expo_data)

    # def job_create_oncoming_notification(self):
    #     """Add job in apscheduler to notify user about oncoming booking via PUSH-notification"""
    #     date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    #     # if (self.date_from - date_now).total_seconds() / 60.0 > BOOKING_PUSH_NOTIFY_UNTIL_MINS:
    #     scheduler.add_job(
    #         func=self.notify_about_oncoming_booking,
    #         name="oncoming",
    #         run_date=self.date_from - timedelta(minutes=BOOKING_PUSH_NOTIFY_UNTIL_MINS) if self.date_from > (
    #                 date_now + timedelta(minutes=BOOKING_PUSH_NOTIFY_UNTIL_MINS)) else date_now + timedelta(
    #             minutes=2),
    #         misfire_grace_time=None,
    #         id="notify_about_oncoming_booking_" + str(self.id),
    #         replace_existing=True
    #     )
    #     scheduler.add_job(
    #         func=self.notify_about_booking_activation,
    #         name="activation",
    #         run_date=self.date_from - timedelta(
    #             minutes=BOOKING_TIMEDELTA_CHECK) if self.date_from > date_now else date_now + timedelta(minutes=3),
    #         misfire_grace_time=None,
    #         id="notify_about_activation_booking_" + str(self.id),
    #         replace_existing=True
    #     )

    # def job_create_change_states(self):
    #     """Add job for occupied/free states changing"""
    #     # scheduler.add_job(
    #     #     self.set_booking_active,
    #     #     "date",
    #     #     run_date=self.date_from,
    #     #     misfire_grace_time=900,
    #     #     id="set_booking_active_" + str(self.id)
    #     # )  # Why we need THIS? Activation is starting when qr code was scanned and then front send request for backend
    #     # date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    #     scheduler.add_job(
    #         self.make_booking_over,
    #         "date",
    #         run_date=self.date_to,
    #         misfire_grace_time=None,
    #         id="set_booking_over_" + str(self.id),
    #         replace_existing=True
    #     )
    #     scheduler.add_job(
    #         self.check_booking_activate,
    #         "date",
    #         run_date=self.date_activate_until,  # date_now + timedelta(minutes=2)
    #         misfire_grace_time=None,
    #         id="check_booking_activate_" + str(self.id),
    #         replace_existing=True
    #     )


class JobStore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_id = models.CharField(max_length=100)
    time_execute = models.DateTimeField()
    parameters = models.JSONField()
    executed = models.BooleanField(default=False)
