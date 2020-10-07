import uuid
from datetime import datetime
from django.db import models
# Local imports
from tables.models import Table
from users.models import User


# Create your models here.
class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_from = models.DateTimeField(default=datetime.utcnow)
    date_to = models.DateTimeField()
    date_activate_until = models.DateTimeField()
    active = models.BooleanField(default=False)
    is_over = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    code = models.IntegerField(default=6593)
    table = models.ForeignKey(Table, related_name="bookings", null=False, on_delete=models.CASCADE)
    theme = models.CharField(default="Без темы", max_length=200)
