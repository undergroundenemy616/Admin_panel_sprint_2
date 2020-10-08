import uuid
from datetime import datetime
from django.db import models
# Local imports
from tables.models import Table
from users.models import User
from django.db.models import Q


# Create your models here.
class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_from = models.DateTimeField(default=datetime.utcnow)
    date_to = models.DateTimeField()
    date_activate_until = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    is_over = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    code = models.IntegerField(default=6593)
    table = models.ForeignKey(Table, related_name="existing_bookings", null=False, on_delete=models.CASCADE)
    theme = models.CharField(default="Без темы", max_length=200)

    @staticmethod
    def check_overflows(table, date_from, date_to):
        """Check for booking availability"""
        overflows = Booking.objects.filter(table=table, is_over=False). \
            filter(Q(date_from__gte=date_from, date_from__lte=date_to)
                   | Q(date_from__lte=date_from, date_to__gte=date_to)
                   | Q(date_from__gte=date_from, date_to__lte=date_to)
                   | Q(date_to__gt=date_from, date_to__lt=date_to))
        if overflows:
            raise ValueError("Table already booked")

    @staticmethod
    def check_is_future(requested_date: datetime):
        """Check if requested date not in past"""
        if requested_date < datetime.utcnow():
            raise ValueError("Cannot create booking in the past")
        return requested_date

