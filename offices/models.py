import uuid

from django.db import models

from files.models import File
from groups.models import Group
from licenses.models import License


class Office(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    working_hours = models.CharField(max_length=128, null=True, blank=True)
    service_email = models.CharField(max_length=256, null=True, blank=True)
    images = models.ManyToManyField(File, related_name='offices')
    license = models.OneToOneField(License, related_name='office', on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(null=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['created_at']

class OfficeZone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=256, null=False, blank=False, default='Зона коворкинга')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False, related_name='zones')
    groups = models.ManyToManyField(Group, related_name='groups')
    is_deletable = models.BooleanField(default=True, blank=False, null=False)

    class Meta:
        unique_together = ['title', 'office']
