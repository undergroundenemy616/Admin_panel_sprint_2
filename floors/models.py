from django.db import models
from offices.models import Office
from files.models import Files


class Floor(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	office = models.ForeignKey(Office, null=False, blank=False, on_delete=models.CASCADE)

	@property
	def occupied(self):
		return sum(rm.occupied for rm in self.rooms.all())

	@property
	def capacity(self):
		return sum(rm.capacity for rm in self.rooms.all())

	@property
	def occupied_tables(self):
		return sum(rm.occupied_tables for rm in self.rooms.all())

	@property
	def capacity_tables(self):
		return sum(rm.capacity_tables for rm in self.rooms.all())

	@property
	def occupied_meeting(self):
		return sum(rm.occupied_meeting for rm in self.rooms.all())

	@property
	def capacity_meeting(self):
		return sum(rm.capacity_meeting for rm in self.rooms.all())


class FloorMap(models.Model):
	image = models.ForeignKey(
		Files,
		on_delete=models.CASCADE,
		blank=False,
		null=False
	)
	floor = models.ForeignKey(Floor, on_delete=models.CASCADE, blank=False, null=False)
