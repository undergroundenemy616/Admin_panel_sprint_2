from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab

# this code copied from manage.py
# set the default Django settings module for the 'celery' app.
from booking_api_django_new import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings')

# you change change the name here
app = Celery("booking_api_django_new")

# read config from Django settings, the CELERY namespace would make celery
# config keys has `CELERY` prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# load tasks.py in django apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.timezone = 'UTC'

app.conf.beat_schedule = {
    'check_booking_status': {
        'task': 'bookings.tasks.check_booking_status',
        'schedule': crontab('0', '0', '*', '*', '*'),
    },
    'transfer_task_to_redis': {
        'task': 'bookings.tasks.transfer_task_to_redis',
        'schedule': crontab('1-59/15', '4-19', '*', '*', '*'),
    },
    'delete_task_from_db': {
        'task': 'bookings.tasks.delete_task_from_db',
        'schedule': crontab('1', '0', '*', '*', '*'),
    },
    'delete_old_statistics': {
        'task': 'files.tasks.delete_old_statistics',
        'schedule': crontab('0', '0', day_of_month='1'),
    },
    'create_bookings_from_exchange': {
        'task': 'bookings.tasks.create_bookings_from_exchange',
        'schedule': crontab(minute='*/1')
    }
}
