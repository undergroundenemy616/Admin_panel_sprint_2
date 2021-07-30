from django.core.mail import send_mail
from django.template.loader import render_to_string

from booking_api_django_new.settings.base import EMAIL_HOST_USER


def send_html_email_message(to: str, subject: str, template_args: dict):
    send_mail(
        recipient_list=[to],
        from_email=EMAIL_HOST_USER,
        subject=subject,
        message='\n'.join([f"{key}: {val}" for key, val in template_args.items()]),
        html_message=render_to_string("mail.html", template_args)
    )


def send_html_email(to: str, subject: str, message: str):
    send_mail(
        recipient_list=[to],
        from_email=EMAIL_HOST_USER,
        subject=subject,
        message=message
    )
