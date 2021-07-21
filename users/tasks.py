from rest_framework.generics import get_object_or_404

from booking_api_django_new.celery import app
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
