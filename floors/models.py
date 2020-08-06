from django.db import models
from offices.models import Office
from files.models import Files


class Floor(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	office = models.ForeignKey(Office, null=False, blank=False, on_delete=models.CASCADE)


class FloorMap(models.Model):
	image = models.ForeignKey(
		Files,
		on_delete=models.CASCADE,
		blank=False,
		null=False
	)
	floor = models.ForeignKey(Floor, on_delete=models.CASCADE, blank=False, null=False)
