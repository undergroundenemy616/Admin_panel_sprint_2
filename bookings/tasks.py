from datetime import timedelta

from django.utils.timezone import now
import bookings.models as bookings
import os
import requests
from booking_api_django_new.settings import PUSH_HOST
from django.core.exceptions import ObjectDoesNotExist
from celery.app.control import Control
from booking_api_django_new.celery import app as celery_app
from django.core.mail import mail_admins
from django_tenants.utils import get_tenant_model, tenant_context


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

    job_execution('check_booking_activate_', uuid)


@celery_app.task()
def make_booking_over(uuid):
    try:
        instance = bookings.Booking.objects.get(id=uuid)
    except ObjectDoesNotExist:
        all_job_delete(uuid)
        return

    flag = {'status': 'auto_over',
            'source': 'make_over'}
    instance.set_booking_over(kwargs=flag)
    all_job_execution(uuid)


@celery_app.task()
def check_booking_status_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            check_booking_status.delay()


@celery_app.task()
def check_booking_status():
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


@celery_app.task()
def notify_about_oncoming_booking(uuid):
    """Send PUSH-notification about oncoming booking to every user devices"""
    push_group = os.environ.get("PUSH_GROUP")
    control = Control(app=celery_app)

    try:
        instance = bookings.Booking.objects.get(id=uuid)
    except ObjectDoesNotExist:
        control.revoke(task_id='make_booking_over_' + str(uuid), terminate=True)
        control.revoke(task_id='check_booking_activate_' + str(uuid), terminate=True)
        control.revoke(task_id='notify_about_activation_booking_' + str(uuid), terminate=True)
        all_job_delete(uuid)
        return

    if push_group and not instance.is_over \
            and instance.user:
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
        response = requests.post(
            PUSH_HOST + "/send_push",
            json=expo_data,
            headers={'content-type': 'application/json'}
        )
        if response.status_code != 200:
            print(f"Unable to send push message for {str(instance.user.id)}: {response.json().get('message')}")
    job_execution('notify_about_oncoming_booking', uuid)


@celery_app.task()
def notify_about_booking_activation(uuid):
    """Send PUSH-notification about opening activation"""
    push_group = os.environ.get("PUSH_GROUP")
    control = Control(app=celery_app)

    try:
        instance = bookings.Booking.objects.get(id=uuid)
    except ObjectDoesNotExist:
        control.revoke(task_id='make_booking_over_' + str(uuid), terminate=True)
        control.revoke(task_id='check_booking_activate_' + str(uuid), terminate=True)
        all_job_delete(uuid)
        return

    if push_group and not instance.is_over \
            and instance.user:
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
        response = requests.post(
            PUSH_HOST + "/send_push",
            json=expo_data,
            headers={'content-type': 'application/json'}
        )
        if response.status_code != 200:
            print(f"Unable to send push message for {str(instance.user.id)}: {response.json().get('message')}")
    job_execution('notify_about_booking_activation', uuid)


@celery_app.task()
def transfer_task_to_redis_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            transfer_task_to_redis.delay()


@celery_app.task()
def transfer_task_to_redis():
    now_time = now() + timedelta(minutes=15)
    job_to_add = bookings.JobStore.objects.filter(time_execute__lte=now_time, executed=False)
    for job in job_to_add:

        func_name = '_'.join(job.job_id.split('_')[:-1])
        globals()[func_name].apply_async(args=[i for i in job.parameters.values()], eta=job.time_execute,
                                         task_id=func_name+'_'+str(job.parameters['uuid']))


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
