import uuid

from django.db import models

from users.models import Account


class PushToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='push_tokens', blank=False, null=False)
    token = models.CharField(max_length=64, null=False, blank=False, unique=True)
