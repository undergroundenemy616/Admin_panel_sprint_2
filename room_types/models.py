from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from offices.models import Office
from files.models import File


class RoomType(models.Model):
    title = models.CharField(max_length=140, null=False)
    office = models.ForeignKey(Office, null=False, on_delete=models.CASCADE)
    color = models.CharField(max_length=8, default="#0079c1")
    icon = models.ForeignKey(File, default=None, on_delete=models.SET_NULL, null=True)
    bookable = models.BooleanField(default=False)
    work_interval_days = models.IntegerField(validators=[MaxValueValidator(90), MinValueValidator(0)], default=0)
    work_interval_hours = models.IntegerField(validators=[MaxValueValidator(24), MinValueValidator(0)], default=0)
    unified = models.BooleanField(default=False)
