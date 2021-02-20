import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.transaction import atomic

from files.models import File
from floors.models import Floor
from room_types.models import RoomType
import tables


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    type = models.ForeignKey('room_types.RoomType', on_delete=models.SET_NULL, related_name='rooms', null=True, blank=False)
    zone = models.ForeignKey('offices.OfficeZone', on_delete=models.SET_NULL, related_name='zones', null=True, blank=False)
    images = models.ManyToManyField(File, related_name='rooms', blank=True)
    floor = models.ForeignKey(Floor, related_name='rooms', null=True, blank=True, on_delete=models.CASCADE)
    seats_amount = models.IntegerField(default=1, null=False, blank=False)
    # is_bookable = models.BooleanField(default=True, null=False, blank=False)

    class Meta:
        ordering = ['floor__title']

# capacity_meeting - floor, office
# capacity_tables - количество столов на floor, office
# occupied_tables - занятые столы на floor, office
# capacity - занятые столы на floor, office


class RoomMarker(models.Model):  # todo added by cybertatar
    room = models.OneToOneField(Room, related_name='room_marker', null=False, blank=False, on_delete=models.CASCADE)
    icon = models.CharField(max_length=64, null=False, blank=False)
    x = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=False,
        blank=False
    )
    y = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=False,
        blank=False
    )

    @atomic()
    def delete(self, using=None, keep_parents=False):
        table = tables.models.Table.objects.filter(room=self.room)
        tables.models.TableMarker.objects.filter(table__in=table).delete()
        super(RoomMarker, self).delete()
