import uuid

from django.db import models

# Create your models here.
from users.models import Account


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(null=True, auto_now_add=True, editable=False)
    title = models.CharField(null=False, blank=False, max_length=200)
    creator = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='teams')
    users = models.ManyToManyField(Account, related_name='teams_users')  # Means Account table
    number = models.IntegerField(default=1, null=False, blank=False)

    class Meta:
        unique_together = ['title', 'creator']

