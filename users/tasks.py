import logging
from rest_framework.generics import get_object_or_404
from booking_api_django_new.celery import app
from mail import send_html_email
from users.broadcasts import SMSBroadcast
from users.models import User


@app.task()
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


@app.task()
def send_email(email, subject, message):
    send_html_email(
        to=email,
        subject=subject,
        message=message
    )


@app.task()
def send_sms(phone_number, message):
    broadcast = SMSBroadcast(phone_number=phone_number)
    broadcast.send(message=message)

    if not broadcast.is_sent:
        logger = logging.getLogger(__name__)
        logger.error(msg="Problem with sending message to: " + str(phone_number))
        raise ValueError("Problem with sending message")
