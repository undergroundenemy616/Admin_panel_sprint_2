import logging

from celery import shared_task
from django.template.loader import render_to_string
from rest_framework.generics import get_object_or_404
from django.core.mail import send_mail

from booking_api_django_new.settings import EMAIL_HOST_USER
from mail import send_html_email
from users.broadcasts import SMSBroadcast
from users.models import User


@shared_task
def send_sms_code(user_id, is_created, code):
    user = get_object_or_404(User, pk=user_id)
    broadcast = SMSBroadcast(phone_number=user.phone_number)
    message = f'Your activation code is: {code}'
    broadcast.send(message=message)  # TODO create celery

    # If something went wrong, user will be deleted and anyway raised exception.
    if not broadcast.is_sent:
        if is_created:
            user.delete()
        raise ValueError('Message was not send!')


@shared_task
def send_email(email, subject, message):
    try:
        send_html_email(
            to=email,
            subject=subject,
            message=message
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(msg=e)


@shared_task
def send_register_email(email, subject, args):
    try:
        send_mail(
            recipient_list=[email],
            from_email=EMAIL_HOST_USER,
            subject=subject,
            message="",
            html_message=render_to_string("mail.html", args)
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(msg=e)


@shared_task
def send_sms(phone_number, message):
    broadcast = SMSBroadcast(phone_number=phone_number)
    broadcast.send(message=message)

    if not broadcast.is_sent:
        logger = logging.getLogger(__name__)
        logger.error(msg="Problem with sending message to: " + str(phone_number))
        raise ValueError("Problem with sending message")
