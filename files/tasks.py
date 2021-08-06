from datetime import timedelta

from django_tenants.utils import get_tenant_model, tenant_context

from booking_api_django_new.celery import app as celery_app

from files.models import File


@celery_app.task()
def delete_old_statistics_in_all_schemas():
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            delete_old_statistics.delay()


@celery_app.task()
def delete_old_statistics():
    stats_for_deleting = File.objects.filter(title__contains='.xlsx')
    stats_for_deleting.delete()
