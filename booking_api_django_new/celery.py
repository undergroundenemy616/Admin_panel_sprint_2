from __future__ import absolute_import
import os
from celery.schedules import crontab
from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp
from celery import Celery
from booking_api_django_new.settings.base import ALLOW_TENANT


# this code copied from manage.py
# set the default Django settings module for the 'celery' app.
from booking_api_django_new import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings')

# you change change the name here
app = TenantAwareCeleryApp("booking_api_django_new") if ALLOW_TENANT else Celery("booking_api_django_new")

# read config from Django settings, the CELERY namespace would make celery
# config keys has `CELERY` prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# load tasks.py in django apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.timezone = 'UTC'

app.conf.beat_schedule = {
    'check_booking_status': {
        'task': 'bookings.check_booking_status_in_all_schemas',
        'schedule': crontab('0', '0', '*', '*', '*'),
    },
    'transfer_task_to_redis': {
        'task': 'bookings.tasks.transfer_task_to_redis_in_all_schemas',
        'schedule': crontab('1-59/15', '4-19', '*', '*', '*'),
    },
    'delete_task_from_db': {
        'task': 'bookings.tasks.delete_task_from_db_in_all_schemas',
        'schedule': crontab('1', '0', '*', '*', '*'),
    },
}
