from django.db import models
from files.models import File
from groups.models import Group
from licenses.models import License


class Office(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    working_hours = models.CharField(max_length=128, null=True, blank=True)
    service_email = models.CharField(max_length=256, null=True, blank=True)
    images = models.ManyToManyField(File, related_name='offices')
    license = models.OneToOneField(License, related_name='office', on_delete=models.PROTECT, null=True)

    def __str__(self):
        return self.title


class OfficeZone(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False, related_name='zones')
    groups = models.ManyToManyField(Group, related_name='groups')
    is_deletable = models.BooleanField(default=True, blank=False, null=False)
