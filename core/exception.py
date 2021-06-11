import os

from django.core.mail import mail_admins
from rest_framework.views import exception_handler
from rest_framework.exceptions import UnsupportedMediaType

from booking_api_django_new.settings import LOCAL, ADMIN_HOST


def detail_exception_handler(exc, context):
    response = exception_handler(exc, context)
    subject = f"Error occurred on {ADMIN_HOST}"

    """
    if we can't parse data from request, then we mock this data
    """
    try:
        request_data = context['request'].data
    except UnsupportedMediaType:
        request_data = {}

    if request_data.get('password'):
        request_data = {}

    if response is not None:
        """
        Get first value in errors dict, and add it to response.
        Values wrapped in list and we extract first value and add it to response dict.
        """
        try:
            error_dict = iter(exc.get_full_details().values())
            error = next(error_dict)
            if isinstance(error, list):
                response.data.update(error[0])
        except AttributeError:
            pass
        if response.status_code >= 500 and not LOCAL:
            subject += f' with code {response.status_code}'
            path = context['request'].get_full_path()
            message = f"User: {str(context['request'].user.id)}\n"
            message += f"Path: {path}\n"
            message += f"Exception: {type(exc).__repr__(exc)}, {exc}\n"
            message += f"Data: {request_data}\n"
            message += f"Response data: {response.data}\n"
            message += f"View: {context['view']}\n"
            mail_admins(subject, message)
    elif not LOCAL:
        message = 'User: Anonymous User\n'
        path = context['request'].get_full_path()
        if hasattr(context['request'].auth, 'payload'):
            message = 'User: ' + str(context['request'].auth.payload['user_id'] + "\n")
        message += f"Path: {path}\n"
        message += f"Exception: {type(exc).__repr__(exc)}, {exc}\n"
        message += f"Data: {request_data}\n"
        message += f"View: {context['view']}\n"
        mail_admins(subject, message)
    return response
