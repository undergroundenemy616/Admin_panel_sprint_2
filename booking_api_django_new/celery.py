from __future__ import absolute_import
import os
from celery.schedules import crontab
from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp
from celery import Celery
from booking_api_django_new.base_settings import ALLOW_TENANT


# this code copied from manage.py
# set the default Django settings module for the 'celery' app.
# you change change the name here

if ALLOW_TENANT:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings.tenant_settings')
    from booking_api_django_new.settings import tenant_settings as settings
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings.non_tenant_settings')
    from booking_api_django_new.settings import non_tenant_settings as settings


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
    'delete_old_statistics': {
        'task': 'files.tasks.delete_old_statistics_in_all_schemas',
        'schedule': crontab('0', '0', day_of_month='1'),
    }
}
