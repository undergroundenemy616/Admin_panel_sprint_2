import uuid

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from users.models import Account


class GroupBooking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Account, null=False, related_name='group_bookings', on_delete=models.CASCADE)
    guests = models.JSONField(encoder=DjangoJSONEncoder, default=list)
