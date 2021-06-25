from celery import shared_task
from rest_framework.generics import get_object_or_404

from mail import send_html_email_message_booking_for_sleep
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
    send_html_email_message_booking_for_sleep(
        to=email,
        subject=subject,
        message=message
    )


@shared_task
def send_sms(phone_number, message):
    broadcast = SMSBroadcast(phone_number=phone_number)
    broadcast.send(message=message)

    if not broadcast.is_sent:
        raise ValueError("Problem with sending message")
