from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
import datetime


class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    paid_until = models.DateField(default=datetime.date.today() + datetime.timedelta(days=5))

    auto_create_schema = True
    auto_drop_schema = True


class Domain(DomainMixin):
    pass
