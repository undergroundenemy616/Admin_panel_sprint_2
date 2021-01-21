from django.db import models
import uuid
from users.models import Account
from offices.models import Office
from files.models import File


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    body = models.TextField()
    images = models.ManyToManyField(File, related_name="report")
    id_delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

