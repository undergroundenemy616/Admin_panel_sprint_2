import uuid
from django.db import models
from django.utils.functional import cached_property
from floors.models import Floor
from files.models import File
from room_types.models import RoomType


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


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    room_type = models.ForeignKey('room_types.RoomType', on_delete=models.SET_NULL, related_name='rooms',
                                  null=True, blank=False)
    images = models.ManyToManyField(File, related_name='rooms', blank=True)
    floor = models.ForeignKey(Floor, related_name='rooms', null=True, blank=True, on_delete=models.CASCADE)
    seats_available = models.IntegerField(default=1, null=False, blank=False)
    is_bookable = models.BooleanField(default=True, null=False, blank=False)

    @cached_property
    def occupied(self):
        """Count of occupied tables."""
        return None  # some logic

    @cached_property
    def capacity(self):
        """Count of tables"""
        return self.tables.count()

    # @cached_property  # todo delete
    # def occupied_tables(self):
    #     """Count of occupied tables in `Рабочее место`."""
    #     if self.room_type.title == "Рабочее место":
    #         return self.tables.filter().count()
    #     return 0

    @cached_property
    def capacity_tables(self):
        """Count of tables in `Рабочее место`."""
        if self.room_type.title == "Рабочее место":
            return self.capacity
        return 0

    # @cached_property
    # def occupied_meeting(self):  # todo delete
    #     """Занятые переговорные"""
    #     if self.room_type.title == "Переговорная":
    #         return self.occupied
    #     return 0

    @cached_property
    def capacity_meeting(self):
        """Количество переговорных на этаже или на офисе."""
        if self.room_type.title == "Переговорная":
            return self.capacity
        return 0

# capacity_meeting - floor, office
# capacity_tables - количество столов на floor, office
# occupied_tables - занятые столы на floor, office
# capacity - занятые столы на floor, office

