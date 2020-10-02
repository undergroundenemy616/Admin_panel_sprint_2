from django.db import models


# Create your models here.
class Booking(models.Model):
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    date_activate_until = models.DateTimeField()
    active = models.BooleanField()
    is_over = models.BooleanField()
    user = models.ForeignKey()
    code = models.IntegerField()
    table = models.ForeignKey()
    theme = models.CharField()