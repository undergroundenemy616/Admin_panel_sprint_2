from django.db import models
from django.core.validators import MinValueValidator


class Files(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	path = models.CharField(max_length=256, null=False, blank=False)
	width = models.IntegerField(null=False, blank=False, validators=[MinValueValidator(0)])
	height = models.IntegerField(null=False, blank=False, validators=[MinValueValidator(0)])