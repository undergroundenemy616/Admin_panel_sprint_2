from django.db import models
from floors.models import Floor
from files.models import Files


class Room(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	description = models.CharField(max_length=256, null=True, blank=True)
	floor = models.ForeignKey(Floor, null=False, blank=False, on_delete=models.CASCADE)


class RoomImage(models.Model):
	file = models.ForeignKey(Files, null=False, blank=False, on_delete=models.CASCADE)
	room = models.ForeignKey(Room, null=False, blank=False, on_delete=models.CASCADE)
