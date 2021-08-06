"""
WSGI config for booking_api_django_new project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

ALLOW_TENANT = os.environ.get('ALLOW_TENANT')

if ALLOW_TENANT:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings.tenant_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings.non_tenant_settings')
application = get_wsgi_application()
