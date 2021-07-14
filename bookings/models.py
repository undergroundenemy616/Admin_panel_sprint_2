import os
import uuid
import asyncio
import orjson
from datetime import datetime, timedelta, timezone

import pytz
import requests
from asgiref.sync import async_to_sync, sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Min, Q
from django.utils.timezone import now

from booking_api_django_new.settings import (BOOKING_PUSH_NOTIFY_UNTIL_MINS,
                                             BOOKING_TIMEDELTA_CHECK,
                                             PUSH_HOST)
from core.scheduler import scheduler
from groups.models import EMPLOYEE_ACCESS
from tables.models import Table
from users.models import Account, User, OfficePanelRelation

from channels.layers import get_channel_layer

MINUTES_TO_ACTIVATE = 15
BOOKING_STATUS_FOR_WS = ['new', 'over', 'canceled']
global GLOBAL_DATE_FROM_WS
global GLOBAL_DATETIME_FROM_WS
global GLOBAL_DATETIME_TO_WS
utc = pytz.UTC
GLOBAL_DATE_FROM_WS = datetime.now().date()
GLOBAL_DATETIME_FROM_WS = datetime.now().replace(tzinfo=utc)
GLOBAL_DATETIME_TO_WS = datetime.utcnow().replace(tzinfo=utc) + timedelta(hours=1)
GLOBAL_TABLES_CHANNEL_NAMES = dict()


class BookingManager(models.Manager):
    def is_overflowed(self, table, date_from, date_to):
        """Check for booking availability"""
        overflows = self.model.objects.filter(table=table, is_over=False, status__in=['waiting', 'active']). \
            filter((Q(date_from__lt=date_to, date_to__gte=date_to)
                    | Q(date_from__lte=date_from, date_to__gt=date_from)
                    | Q(date_from__gte=date_from, date_to__lte=date_to)) & Q(
            date_from__lt=date_to))
        if overflows:
            return True
        return False

    def is_overflowed_with_data(self, table, date_from, date_to):
        """Check for booking availability"""
        overflows = self.model.objects.filter(table=table). \
            filter((Q(date_from__lt=date_to, date_to__gte=date_to)
                    | Q(date_from__lte=date_from, date_to__gt=date_from)
                    | Q(date_from__gte=date_from, date_to__lte=date_to)) & Q(date_from__lt=date_to))
        return overflows

    def is_user_overflowed(self, account, room_type, date_from, date_to):
        try:
            access = account.groups.aggregate(Min('access')) if account.groups.exists() else {
                'access__min': EMPLOYEE_ACCESS}
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
    objects = BookingManager()

    def save(self, *args, **kwargs):
        self.date_activate_until = self.calculate_date_activate_until()
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.job_create_change_states()
        if self.table.room.type.unified:
            if GLOBAL_DATE_FROM_WS == self.date_from.date():
                result_for_date = self.create_response_for_date_websocket()
                try:
                    asyncio.run(self.websocket_notification_by_date(result_for_date))
                except Exception as e:
                    pass
            else:
                pass
            if ((GLOBAL_DATETIME_FROM_WS < self.date_to <= GLOBAL_DATETIME_TO_WS)
                    or (GLOBAL_DATETIME_FROM_WS <= self.date_from < GLOBAL_DATETIME_TO_WS)
                    or (GLOBAL_DATETIME_FROM_WS >= self.date_from >= GLOBAL_DATETIME_TO_WS)
                    and (GLOBAL_DATETIME_FROM_WS < self.date_to)):
                result_for_datetime = self.create_response_for_datetime_websocket()
                try:
                    asyncio.run(self.websocket_notification_by_datetime(result_for_datetime))
                except Exception as e:
                    pass
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
                instance.date_to = now()
        else:
            instance.date_to = now()
            instance.status = 'canceled'
        instance.table.set_table_free()
        # instance = super(self.__class__, self)
        if scheduler.get_job(job_id="notify_about_oncoming_booking_" + str(self.id)):
            scheduler.remove_job(job_id="notify_about_oncoming_booking_" + str(self.id))
        if scheduler.get_job(job_id="notify_about_activation_booking_" + str(self.id)):
            scheduler.remove_job(job_id="notify_about_activation_booking_" + str(self.id))
        if scheduler.get_job(job_id="check_booking_activate_" + str(self.id)):
            scheduler.remove_job(job_id="check_booking_activate_" + str(self.id))
        if scheduler.get_job(job_id="set_booking_over_" + str(self.id)):
            scheduler.remove_job(job_id="set_booking_over_" + str(self.id))
        super(Booking, instance).save()
        if self.table.room.type.unified:
            if GLOBAL_DATE_FROM_WS == self.date_from.date():
                result_for_date = self.create_response_for_date_websocket(instance)
                try:
                    asyncio.run(self.websocket_notification_by_date(result=result_for_date))
                except Exception as e:
                    pass
            else:
                pass
            if ((GLOBAL_DATETIME_FROM_WS < self.date_to <= GLOBAL_DATETIME_TO_WS)
                    or (GLOBAL_DATETIME_FROM_WS <= self.date_from < GLOBAL_DATETIME_TO_WS)
                    or (GLOBAL_DATETIME_FROM_WS >= self.date_from >= GLOBAL_DATETIME_TO_WS)
                    and (GLOBAL_DATETIME_FROM_WS < self.date_to)):
                result_for_datetime = self.create_response_for_datetime_websocket(instance)
                try:
                    asyncio.run(self.websocket_notification_by_datetime(result_for_datetime))
                except Exception as e:
                    pass

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
        if push_group and not self.is_over \
                and self.user:
            expo_data = {
                "account": str(self.user.id),
                "app": push_group,
                "expo": {
                    "title": "Открыто подтверждение!",
                    "body": f"Вы можете подтвердить бронирование QR-кодом в течение 30 минут.",
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

    def job_create_oncoming_notification(self):
        """Add job in apscheduler to notify user about oncoming booking via PUSH-notification"""
        date_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        # if (self.date_from - date_now).total_seconds() / 60.0 > BOOKING_PUSH_NOTIFY_UNTIL_MINS:
        scheduler.add_job(
            func=self.notify_about_oncoming_booking,
            name="oncoming",
            run_date=self.date_from - timedelta(minutes=BOOKING_PUSH_NOTIFY_UNTIL_MINS) if self.date_from > (
                    date_now + timedelta(minutes=BOOKING_PUSH_NOTIFY_UNTIL_MINS)) else date_now + timedelta(
                minutes=2),
            misfire_grace_time=None,
            id="notify_about_oncoming_booking_" + str(self.id),
            replace_existing=True
        )
        scheduler.add_job(
            func=self.notify_about_booking_activation,
            name="activation",
            run_date=self.date_from - timedelta(
                minutes=BOOKING_TIMEDELTA_CHECK) if self.date_from > date_now else date_now + timedelta(minutes=3),
            misfire_grace_time=None,
            id="notify_about_activation_booking_" + str(self.id),
            replace_existing=True
        )

    @staticmethod
    async def websocket_notification_by_date(result=None):
        json_format = {'type': 'send_json',
                       'text': {
                        'type': 'timeline',
                        'data': result
                             }
                       }
        channel_layer = get_channel_layer()
        print("existing_booking", json_format)
        result_in_json = orjson.loads(orjson.dumps(json_format))
        print('GLOBAL_TABLES', GLOBAL_TABLES_CHANNEL_NAMES)
        print('Send info outside model')
        channel = GLOBAL_TABLES_CHANNEL_NAMES[f"{result['table_id']}"]
        await channel_layer.send(str(channel), result_in_json)

    @staticmethod
    async def websocket_notification_by_datetime(result=None):
        json_format = {
            'type': 'send_json',
            'text': {
                'type': 'meeting_block',
                'data': result
            }
        }
        channel_layer = get_channel_layer()
        result_in_json = orjson.loads(orjson.dumps(json_format))
        channel = GLOBAL_TABLES_CHANNEL_NAMES[f"{result['table_id']}"]
        await channel_layer.send(str(channel), result_in_json)

    def create_response_for_datetime_websocket(self, instance=None):
        local_tz = pytz.timezone('Europe/Moscow')
        result = []
        if self.status == 'active' and not instance:
            result.append({
                'status': 'occupied',
                'id': str(self.id),
                'table_id': str(self.table.id),
                'title': str(self.table.room.title),
                'date_from': str(self.date_from.astimezone(local_tz))[:16],
                'date_to': str(self.date_to.astimezone(local_tz))[:16],
                'user': {
                    'id': str(self.user.id),
                    'phone': str(self.user.user.phone_number),
                    'firstname': str(self.user.first_name),
                    'lastname': str(self.user.last_name),
                    'middlename': str(self.user.middle_name),
                },
                'theme': str(self.theme)
            })
        elif instance:
            image = self.table.images.first()
            if image:
                result.append({
                    'id': str(self.table.room.id),
                    'title': str(self.table.room.title),
                    'table_id': str(self.table.id),
                    'tables': [
                        {'id': str(self.table.id),
                         'title': str(self.table.title),
                         'is_occupied': str(False)}
                    ],
                    'images': [{
                        'id': str(image.id) if image else None,
                        'title': str(image.title) if image else None,
                        'path': str(image.path) if image else None,
                        'thumb': str(image.thumb) if image else None
                    }],
                    'status': 'not occupied'
                })
            else:
                result.append({
                    'id': str(self.table.room.id),
                    'title': str(self.table.room.title),
                    'table_id': str(self.table.id),
                    'tables': [
                        {'id': str(self.table.id),
                         'title': str(self.table.title),
                         'is_occupied': str(False)}
                    ],
                    'images': [],
                    'status': 'not occupied'
                })
        return result

    def create_response_for_date_websocket(self, instance=None):
        try:
            panel = OfficePanelRelation.objects.get(room_id=self.table.room_id)
        except OfficePanelRelation.DoesNotExist:
            return
        existing_booking = Booking.objects.filter(table=self.table_id,
                                                  status__in=['waiting', 'active'],
                                                  date_from__year=str(self.date_from.year),
                                                  date_from__month=str(self.date_from.month),
                                                  date_from__day=str(self.date_from.day))
        result = []
        local_tz = pytz.timezone('Europe/Moscow')
        for booking in existing_booking:
            if instance and instance.id == booking.id:
                continue
            result.append({
                'id': str(booking.id),
                'table_id': str(booking.table.id),
                'date_from': str(booking.date_from.astimezone(local_tz))[0:16],
                'date_to': str(booking.date_to.astimezone(local_tz))[0:16]
            })
        if not instance:
            result.append({
                'id': str(self.id),
                'table_id': str(self.table.id),
                'date_from': str(self.date_from.astimezone(local_tz))[0:16],
                'date_to': str(self.date_to.astimezone(local_tz))[0:16]
            })
        return result

    def job_create_change_states(self):
        """Add job for occupied/free states changing"""
        scheduler.add_job(
            self.make_booking_over,
            "date",
            run_date=self.date_to,
            misfire_grace_time=10000,
            id="set_booking_over_" + str(self.id),
            replace_existing=True
        )
        # scheduler.add_job(
        #     self.check_booking_activate,
        #     "date",
        #     run_date=self.date_activate_until,  # date_now + timedelta(minutes=2)
        #     misfire_grace_time=10000,
        #     id="check_booking_activate_" + str(self.id),
        #     replace_existing=True
        # )
