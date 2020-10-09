import uuid
from django.db import models
from django.utils.functional import cached_property
from floors.models import Floor
from files.models import File


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    type = models.CharField(max_length=128, null=False, blank=False)  # Todo change
    floor = models.ForeignKey(Floor, related_name='rooms', null=True, blank=True, on_delete=models.CASCADE)

    @cached_property
    def occupied(self):
        """Count of occupied tables."""
        return self.tables.filter(is_occupied=True).count()

    @cached_property
    def capacity(self):
        """Count of tables"""
        return self.tables.count()

    @cached_property
    def occupied_tables(self):
        """Count of occupied tables in `Рабочее место`."""
        if self.type == "Рабочее место":
            return self.occupied
        return 0

    @cached_property
    def capacity_tables(self):
        """Count of tables in `Рабочее место`."""
        if self.type == "Рабочее место":
            return self.capacity
        return 0

    @cached_property
    def occupied_meeting(self):
        if self.type == "Переговорная":
            return self.occupied
        return 0

    @cached_property
    def capacity_meeting(self):
        if self.type == "Переговорная":
            return self.capacity
        return 0


# class RoomImage(models.Model):
# 	file = models.ForeignKey(File, null=False, blank=False, on_delete=models.CASCADE)
# 	room = models.ForeignKey(Room, null=False, blank=False, on_delete=models.CASCADE)


# class RoomMarker(models.Model):  # todo added by cybertatar
#     room = models.OneToOneField(Room, null=False, blank=False, on_delete=models.CASCADE)
#     icon = models.CharField(max_length=64, null=False, blank=False)
#     x = models.DecimalField(
#         max_digits=4,
#         decimal_places=2,
#         validators=[MinValueValidator(0)],
#         null=False,
#         blank=False
#     )
