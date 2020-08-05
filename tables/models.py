from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from rooms.models import Room
from users.models import User
from files.models import Files


class TableTag(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	icon = models.ForeignKey(
		Files,
		on_delete=models.CASCADE,
		blank=True,
		null=True
	)


class Table(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	description = models.CharField(max_length=256, null=True, blank=True)
	room = models.ForeignKey(Room, on_delete=models.CASCADE, blank=False, null=False)
	status = models.CharField(max_length=64, null=True, blank=True)
	tags = models.ManyToManyField(TableTag, null=True, blank=True)


class Rating(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
	table = models.ForeignKey(Table, on_delete=models.CASCADE, blank=False, null=False)
	rating = models.DecimalField(
		max_digits=3,
		decimal_places=2,
		validators=[MinValueValidator(0), MaxValueValidator(5)],
		null=False,
		blank=False
	)
