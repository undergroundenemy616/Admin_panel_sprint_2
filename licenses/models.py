from django.core.validators import MinValueValidator
from django.db import models


class License(models.Model):
    issued_at = models.DateField(blank=True, null=True)
    expires_at = models.DateField(blank=True, null=True)
    support_available = models.DateField(blank=True, null=True)
    support_expires_at = models.DateField(blank=True, null=True)
    tables_available = models.IntegerField(validators=[MinValueValidator(0)], blank=True, null=True)
    tables_infinite = models.BooleanField(blank=False, null=False)
    forever = models.BooleanField(blank=False, null=False)

    # office = models.OneToOneField(Office, on_delete=models.CASCADE, related_query_name='licenses',
    #                               blank=True, null=True)
