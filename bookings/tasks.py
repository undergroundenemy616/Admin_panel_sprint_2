from datetime import timedelta
from django.db import connection
from datetime import timedelta, datetime

import pytz
from django.core.exceptions import ValidationError as ValErr
from django.core.validators import validate_email
from django.db.models import Q
from django.utils.timezone import now
from exchangelib import Account as Ac, Credentials, Configuration, DELEGATE
from exchangelib.errors import UnauthorizedError, TransportError
from exchangelib.services import GetRooms

import bookings.models as bookings
import os
import requests
from booking_api_django_new.base_settings import PUSH_HOST
from django.core.exceptions import ObjectDoesNotExist
from celery.app.control import Control
import logging
from booking_api_django_new.celery import app as celery_app
from django.core.mail import mail_admins
from django_tenants.utils import get_tenant_model, tenant_context

from group_bookings.models import GroupBooking
from tables.models import Table
from users.models import Account
from users.tasks import send_email


def all_job_delete(uuid):
    for job in bookings.JobStore.objects.filter(job_id__contains=str(uuid)):
        job.delete()


def job_execution(job_name, uuid):
    job = bookings.JobStore.objects.filter(job_id=job_name+str(uuid))
    if job:
        job[0].executed = True
        job[0].save()


def all_job_execution(uuid):
    for job in bookings.JobStore.objects.filter(job_id__contains=str(uuid)):
        job.executed = True
        job.save()


@celery_app.task()
def check_booking_activate(uuid):
    control = Control(app=celery_app)
    logger = logging.getLogger(__name__)
    logger.info(msg="Execute check_booking_activate "+str(uuid))
    try:
        try:
            instance = bookings.Booking.objects.get(id=uuid)
        except ObjectDoesNotExist:
            control.revoke(task_id='make_booking_over_' + str(uuid), terminate=True)
            all_job_delete(uuid)
            return

        if not instance.is_active:
            flag = {'status': 'auto_canceled',
                    'source': 'check_activate'}
            instance.set_booking_over(kwargs=flag)

            control.revoke(task_id='make_booking_over_' + str(uuid), terminate=True)
            all_job_execution(uuid)
    except Exception as e:
        logger.error(msg=f"Error check_booking_activate: {e}")
    job_execution('check_booking_activate_', uuid)


@celery_app.task()
def make_booking_over(uuid):
    logger = logging.getLogger(__name__)
    logger.info(msg="Start make_booking_over "+str(uuid))
    try:
        try:
            instance = bookings.Booking.objects.get(id=uuid)
        except ObjectDoesNotExist:
            all_job_delete(uuid)
            return

        flag = {'status': 'auto_over',
                'source': 'make_over'}
        instance.set_booking_over(kwargs=flag)
        all_job_execution(uuid)
    except Exception as e:
        logger.error(msg=f"Error make_booking_over: {e}")
    logger.info(msg="Finish make_booking_over " + str(uuid))


@celery_app.task()
def check_booking_status_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            check_booking_status.delay()


@celery_app.task()
def check_booking_status():
    logger = logging.getLogger(__name__)
    logger.info(msg="Start check_booking_status")
    try:
        now_date = now()
        subject = 'About booking on ' + os.environ.get('ADMIN_HOST')
        bad_status = ['active', 'waiting']
        query_booking = bookings.Booking.objects.filter(date_activate_until__lt=now_date, status__in=bad_status)
        if len(query_booking) > 0:
            message = 'Amount of bad bookings: ' + str(len(query_booking)) + '\n'
            message += 'ids: \n'
            for book in query_booking:
                book.is_over = True
                book.is_active = False
                book.status = 'over'
                book.save()
                message += str(book.id) + '\n'
            mail_admins(subject, message)
    except Exception as e:
        logger.error(msg=f"Error check_booking_status: {e}")
    logger.info(msg="Finish check_booking_status ")


@celery_app.task()
def notify_about_oncoming_booking(uuid, language):
    logger = logging.getLogger(__name__)
    logger.info(msg="Execute notify_about_oncoming_booking "+str(uuid))
    """Send PUSH-notification about oncoming booking to every user devices"""
    schema = connection.schema_name if os.environ.get('ALLOW_TENANT') else os.environ.get("PUSH_GROUP")
    push_group = f"simpleoffice-{schema}"
    control = Control(app=celery_app)

    try:
        instance = bookings.Booking.objects.get(id=uuid)
    except ObjectDoesNotExist:
        control.revoke(task_id='make_booking_over_' + str(uuid), terminate=True)
        control.revoke(task_id='check_booking_activate_' + str(uuid), terminate=True)
        control.revoke(task_id='notify_about_activation_booking_' + str(uuid), terminate=True)
        control.revoke(task_id='notify_about_book_ending_' + str(uuid), terminate=True)
        all_job_delete(uuid)
        return

    if push_group and not instance.is_over \
            and instance.user:
        if language == 'ru':
            expo_data = {
                "account": str(instance.user.id),
                "app": push_group,
                "expo": {
                    "title": "Уведомление о предстоящем бронировании",
                    "body": f"Ваше бронирование начнется меньше чем через час. Не забудьте отсканировать QR-код для подтверждения.",
                    "data": {
                        "go_booking": True
                    }
                }
            }
        else:
            expo_data = {
                "account": str(instance.user.id),
                "app": push_group,
                "expo": {
                    "title": "Notification about upcoming booking",
                    "body": f"Your booking will start in less than an hour. Don't forget to scan QR for confirmation.",
                    "data": {
                        "go_booking": True
                    }
                }
            }
        response = requests.post(
            PUSH_HOST + "/send_push",
            json=expo_data,
            headers={'content-type': 'application/json'}
        )
        if response.status_code != 200:
            logger.info(msg="Problem with push sending: " + str(uuid))
    else:
        logger.info(msg="Problem with push group or booking is over: " + str(uuid))
    job_execution('notify_about_oncoming_booking_', uuid)


@celery_app.task()
def notify_about_booking_activation(uuid, language):
    logger = logging.getLogger(__name__)
    logger.info(msg=f"Execute notify_about_booking_activation {str(uuid)} for tenant {connection.schema_name}")
    """Send PUSH-notification about opening activation"""
    schema = connection.schema_name if os.environ.get('ALLOW_TENANT') else os.environ.get("PUSH_GROUP")
    push_group = f"simpleoffice-{schema}"
    control = Control(app=celery_app)

    try:
        instance = bookings.Booking.objects.get(id=uuid)
    except ObjectDoesNotExist:
        control.revoke(task_id='make_booking_over_' + str(uuid), terminate=True)
        control.revoke(task_id='check_booking_activate_' + str(uuid), terminate=True)
        control.revoke(task_id='notify_about_book_ending_' + str(uuid), terminate=True)
        all_job_delete(uuid)
        return

    if push_group and not instance.is_over \
            and instance.user:
        if language == 'ru':
            expo_data = {
                "account": str(instance.user.id),
                "app": push_group,
                "expo": {
                    "title": "Открыто подтверждение!",
                    "body": "Вы можете подтвердить бронирование QR-кодом в течение 30 минут.",
                    "data": {
                        "go_booking": True
                    }
                }
            }
        else:
            expo_data = {
                "account": str(instance.user.id),
                "app": push_group,
                "expo": {
                    "title": "Confirmation is open!",
                    "body": "You can confirm your booking by QR in 30 minutes",
                    "data": {
                        "go_booking": True
                    }
                }
            }
        response = requests.post(
            PUSH_HOST + "/send_push",
            json=expo_data,
            headers={'content-type': 'application/json'}
        )
        if response.status_code != 200:
            logger.info(msg="Problem with push sending: " + str(uuid))
    else:
        logger.info(msg="Problem with push group or booking is over: " + str(uuid))
    job_execution('notify_about_booking_activation_', uuid)


@celery_app.task()
def notify_about_book_ending(uuid, language):
    logger = logging.getLogger(__name__)
    logger.info(msg="Execute notify_about_book_ending " + str(uuid))

    schema = connection.schema_name if os.environ.get('ALLOW_TENANT') else os.environ.get("PUSH_GROUP")
    push_group = f"simpleoffice-{schema}"
    control = Control(app=celery_app)
    try:
        instance = bookings.Booking.objects.get(id=uuid)
    except ObjectDoesNotExist:
        control.revoke(task_id='make_booking_over_' + str(uuid), terminate=True)
        all_job_delete(uuid)
        return

    if push_group and not instance.is_over \
            and instance.user:
        if language == 'ru':
            expo_data = {
                "account": str(instance.user.id),
                "app": push_group,
                "expo": {
                    "title": "Бронирование подходит к концу!",
                    "body": "Ваша бронирование заканчивается через 15 минут.",
                    "data": {
                        "go_booking": True
                    }
                }
            }
        else:
            expo_data = {
                "account": str(instance.user.id),
                "app": push_group,
                "expo": {
                    "title": "Your booking is coming to the end!",
                    "body": "Your booking ends in 15 minutes.",
                    "data": {
                        "go_booking": True
                    }
                }
            }
        response = requests.post(
            PUSH_HOST + "/send_push",
            json=expo_data,
            headers={'content-type': 'application/json'}
        )
        if response.status_code != 200:
            logger.info(msg="Problem with push sending: " + str(uuid))
    else:
        logger.info(msg="Problem with push group or booking is over:" + str(uuid))

    job_execution('notify_about_book_ending_', uuid)


@celery_app.task()
def transfer_task_to_redis_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            transfer_task_to_redis.delay()


@celery_app.task()
def transfer_task_to_redis():
    logger = logging.getLogger(__name__)
    logger.info(msg="Start transfer_task_to_redis")
    try:
        now_time = now() + timedelta(minutes=15)
        job_to_add = bookings.JobStore.objects.filter(time_execute__lte=now_time, executed=False)
        for job in job_to_add:

            func_name = '_'.join(job.job_id.split('_')[:-1])
            task_id = str(job.parameters['uuid'])
            if 'notify' in func_name and len(job.parameters) < 2:
                job.parameters['language'] = 'ru'
            globals()[func_name].apply_async(args=[i for i in job.parameters.values()], eta=job.time_execute,
                                             task_id=func_name+'_'+task_id)
            logger.info(msg=f'Add task: {func_name}_{task_id}')
    except Exception as e:
        logger.error(msg=f"Error transfer_task_to_redis: {e}")
    logger.info(msg="Finish transfer_task_to_redis")


@celery_app.task()
def delete_task_from_db_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            delete_task_from_db.delay()


@celery_app.task()
def delete_task_from_db():
    job_to_delete = bookings.JobStore.objects.filter(executed=True)
    for job in job_to_delete:
        job.delete()


@celery_app.task()
def create_bookings_from_exchange_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            create_bookings_from_exchange.delay()


@celery_app.task()
def create_bookings_from_exchange():
    logger = logging.getLogger(__name__)
    try:
        queryset = Account.objects.all().select_related('user')
        credentials = Credentials(os.environ['EXCHANGE_ADMIN_LOGIN'], os.environ['EXCHANGE_ADMIN_PASS'])
        config = Configuration(server=os.environ['EXCHANGE_SERVER'], credentials=credentials)
        account = Ac(primary_smtp_address=os.environ['EXCHANGE_ADMIN_LOGIN'], config=config, autodiscover=False,
                     access_type=DELEGATE)
        start = datetime(datetime.now().year, 1, 1, 0, 0, tzinfo=account.default_timezone)
        end = datetime(datetime.now().year, 12, 31, 23, 59, tzinfo=account.default_timezone)
        rooms_data = []
        room_lists = account.protocol.get_roomlists()
        calendar_view = list(account.calendar.view(start=start, end=end))
        for room_list in room_lists:
            rooms = GetRooms(protocol=account.protocol).call(roomlist=room_list)
            for room in rooms:
                rooms_data.append({
                    "title": room.name,
                    "email": room.email_address
                })
                room_account = Ac(primary_smtp_address=room.email_address, config=config, autodiscover=False,
                                  access_type=DELEGATE)
                calendar_view = calendar_view + list(room_account.calendar.view(start=start, end=end))
        for f in calendar_view:
            if f.is_meeting:
                author_email = f.organizer.email_address
                date_to = pytz.UTC.localize(datetime.strptime(str(f.end).split('+')[0], "%Y-%m-%d %H:%M:%S"))
                date_from = pytz.UTC.localize(datetime.strptime(str(f.start).split('+')[0], "%Y-%m-%d %H:%M:%S"))
                timezone = pytz.timezone(str(f._start_timezone))
                message_date_from = timezone.localize(datetime.strptime(str(f.end).split('+')[0], "%Y-%m-%d %H:%M:%S"))
                message_date_to = timezone.localize(datetime.strptime(str(f.start).split('+')[0], "%Y-%m-%d %H:%M:%S"))
                room_title = f.location
                room_email = None
                users = [{
                    "email": f.organizer.email_address,
                    "name": f.organizer.name
                }]
                user_emails = [f.organizer.email_address]
                guests = []
                if f.required_attendees:
                    for attendee in f.required_attendees:
                        if Account.objects.filter(Q(email=attendee.mailbox.email_address)
                                                  |
                                                  Q(user__email=attendee.mailbox.email_address)).exists():
                            users.append({
                                "email": attendee.mailbox.email_address,
                                "name": attendee.mailbox.name
                            })
                            user_emails.append(attendee.mailbox.email_address)
                        else:
                            guests.append({
                                attendee.mailbox.name: attendee.mailbox.email_address,
                            })
                            try:
                                validate_email(attendee.mailbox.email_address)
                                message = f"Здравствуйте, {attendee.mailbox.name}. Вы были приглашены на встречу, " \
                                          f"которая пройдёт в {f.location}. " \
                                          f"Дата и время проведения {datetime.strftime(message_date_from, '%d.%m.%Y %H:%M')}-" \
                                          f"{datetime.strftime(message_date_to, '%H:%M')}"
                                send_email.delay(email=attendee.mailbox.email_address, subject="Встреча", message=message)
                            except ValErr:
                                pass
                for room in rooms_data:
                    if room['title'] in room_title:
                        room_email = room['email']
                users = {user['email']: user for user in users}.values()
                if room_email:
                    try:
                        table = Table.objects.get(room__exchange_email=room_email, room__type__unified=True)
                        if not bookings.Booking.objects.is_overflowed(table, date_to=date_to, date_from=date_from):
                            author = queryset.get(Q(email=author_email)
                                                  |
                                                  Q(user__email=author_email))
                            group_booking = GroupBooking.objects.create(author=author, guests=guests)
                            users_objects = queryset.filter(Q(email__in=list(set(user_emails)))
                                                            |
                                                            Q(user__email__in=user_emails))
                            for i in range(len(users)):
                                booking = bookings.Booking(
                                    date_to=date_to,
                                    date_from=date_from,
                                    table=table,
                                    user=users_objects.all()[i],
                                    group_booking=group_booking,
                                    theme=f.subject
                                )
                                booking.save()
                    except (Table.DoesNotExist, Account.DoesNotExist):
                        pass
    except KeyError:
        logger.error(msg="Exchange login, password or server wasn`t provided")
    except UnauthorizedError:
        logger.error(msg="Wrong login or password")
    except TransportError:
        logger.error(msg=f"Unable to connect to exchange server: {os.environ['EXCHANGE_SERVER']}")
    except Exception as e:
        logger.error(msg=f"Something went wrong \n{e}")


@celery_app.task()
def delete_group_bookings_that_not_in_calendar_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            delete_group_bookings_that_not_in_calendar.delay()


@celery_app.task()
def delete_group_bookings_that_not_in_calendar():
    logger = logging.getLogger(__name__)
    try:
        credentials = Credentials(os.environ['EXCHANGE_ADMIN_LOGIN'], os.environ['EXCHANGE_ADMIN_PASS'])
        config = Configuration(server=os.environ['EXCHANGE_SERVER'], credentials=credentials)
        account_exchange = Ac(primary_smtp_address=os.environ['EXCHANGE_ADMIN_LOGIN'], config=config,
                              autodiscover=False, access_type=DELEGATE)

        start = datetime(datetime.now().year, datetime.now().month, datetime.now().day, tzinfo=pytz.UTC)
        end = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 23, 59, tzinfo=pytz.UTC)

        bookings_to_check = bookings.Booking.objects.filter(Q(date_from__date=start.date())
                                                            &
                                                            Q(date_to__date=end.date())
                                                            &
                                                            Q(table__room__exchange_email__isnull=False))

        bookings_in_exchange = []
        calendar_items = list(account_exchange.calendar.filter(start__range=(start, end)))
        room_lists = account_exchange.protocol.get_roomlists()
        for room_list in room_lists:
            rooms = GetRooms(protocol=account_exchange.protocol).call(roomlist=room_list)
            for room in rooms:
                room_account = Ac(primary_smtp_address=room.email_address, config=config,
                                  autodiscover=False, access_type=DELEGATE)
                calendar_items = calendar_items + list(room_account.calendar.filter(start__range=(start, end)))
        for booking in bookings_to_check:
            for calendar_item in calendar_items:
                if booking.table.room.exchange_email == calendar_item.location and \
                        booking.date_from == calendar_item.start and booking.date_to == calendar_item.end:
                    bookings_in_exchange.append(booking.id)

            group_bookings = GroupBooking.objects.filter(~Q(bookings__id__in=bookings_in_exchange)
                                                         &
                                                         Q(bookings__table__room__exchange_email__isnull=False)). \
                distinct()

            if group_bookings:
                group_bookings.delete()
    except KeyError:
        logger.error(msg="Exchange login, password or server wasn`t provided")
    except UnauthorizedError:
        logger.error(msg="Wrong login or password")
    except TransportError:
        logger.error(msg=f"Unable to connect to exchange server: {os.environ['EXCHANGE_SERVER']}")
    except Exception as e:
        logger.error(msg=f"Something went wrong \n{e}")


@celery_app.task()
def exchange_booking_cancel(instance):
    logger = logging.getLogger(__name__)
    if instance.bookings.all()[0].table.room.exchange_email:
        try:
            credentials = Credentials(os.environ['EXCHANGE_ADMIN_LOGIN'], os.environ['EXCHANGE_ADMIN_PASS'])
            config = Configuration(server=os.environ['EXCHANGE_SERVER'], credentials=credentials)
            account_exchange = Ac(primary_smtp_address=os.environ['EXCHANGE_ADMIN_LOGIN'], config=config,
                                  autodiscover=False, access_type=DELEGATE)
            date_from = instance.bookings.all()[0].date_from
            date_to = instance.bookings.all()[0].date_to
            start = datetime(date_from.year, date_from.month,
                             date_from.day, date_from.hour,
                             date_from.minute, tzinfo=pytz.UTC)
            end = datetime(date_to.year, date_to.month,
                           date_to.day, date_to.hour,
                           date_to.minute, tzinfo=pytz.UTC)
            for calendar_item in account_exchange.calendar.filter(start=start, end=end):
                if calendar_item.organizer.email_address == account_exchange.primary_smtp_address and \
                        instance.bookings.all()[0].table.room.exchange_email == calendar_item.location:
                    calendar_item.cancel()
        except KeyError:
            logger.error(msg="Exchange login, password or server wasn`t provided")
        except UnauthorizedError:
            logger.error(msg="Wrong login or password")
        except TransportError:
            logger.error(msg=f"Unable to connect to exchange server: {os.environ['EXCHANGE_SERVER']}")
        except Exception as e:
            logger.error(msg=f"Something went wrong \n{e}")
