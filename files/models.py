import uuid

from django.db import models


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    path = models.CharField(max_length=256, null=False, blank=False)
    thumb = models.CharField(max_length=256, null=True, blank=True)
    size = models.CharField(max_length=10, null=False, blank=False)

# width = models.IntegerField(null=False, blank=False, validators=[MinValueValidator(0)])
# height = models.IntegerField(null=False, blank=False, validators=[MinValueValidator(0)])
