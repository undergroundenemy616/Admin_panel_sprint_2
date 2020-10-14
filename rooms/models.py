import uuid
from django.core.validators import MinValueValidator
from django.db import models
from floors.models import Floor
from files.models import File
from room_types.models import RoomType


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


# capacity_meeting - floor, office
# capacity_tables - количество столов на floor, office
# occupied_tables - занятые столы на floor, office
# capacity - занятые столы на floor, office


class RoomMarker(models.Model):  # todo added by cybertatar
    room = models.OneToOneField(Room, null=False, blank=False, on_delete=models.CASCADE)
    icon = models.CharField(max_length=64, null=False, blank=False)
    x = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=False,
        blank=False
    )
