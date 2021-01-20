import uuid

from django.db import models

from files.models import File
from offices.models import Office


class Floor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=1024, null=True, blank=True)
    office = models.ForeignKey(Office, related_name='floors', null=False, blank=False, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class FloorMap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    image = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )
    height = models.CharField(max_length=12, null=True, blank=False)
    width = models.CharField(max_length=12, null=True, blank=False)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, blank=False, null=True)

    def __str__(self):
        return f'{self.id}: {self.width}x{self.height}'
