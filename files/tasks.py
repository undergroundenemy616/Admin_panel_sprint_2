from datetime import timedelta

from celery import shared_task

from files.models import File


@shared_task()
def delete_old_statistics():
    stats_for_deleting = File.objects.filter(title__contains='.xlsx')
    stats_for_deleting.delete()
