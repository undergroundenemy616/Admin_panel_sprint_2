from django.db import models
from offices.models import Office
from files.models import File


class Floor(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False, unique=True)
    description = models.CharField(max_length=1024, null=True, blank=True)
    office = models.ForeignKey(Office, related_name='floors', null=False, blank=False, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class FloorMap(models.Model):
    image = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )
    height = models.CharField(max_length=12, null=False, blank=False)
    width = models.CharField(max_length=12, null=False, blank=False)
    floor = models.OneToOneField(Floor, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return f'{self.id}: {self.width}x{self.height}'
