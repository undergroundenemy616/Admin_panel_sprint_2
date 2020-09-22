from typing import List, Optional

from django.db import models
from django.db.models import Manager

from floors.models import Floor
from files.models import File


class RoomManager(Manager):
    def filtered_rooms(self, floor_id, typed: Optional[str] = None, tags: Optional[List] = None):
        assert tags is not None and isinstance(tags, list) and len(tags), (
            'Error'
        )
        row = """select r.id,
                       r.title,
                       r.description::varchar(256),
                       r.type::varchar(64),
                       (select count(*) from tables_table)::integer                              as "capacity",
                       (select count(*) from tables_table t where t.is_occupied = True)::integer as "occupied",
                       (select case
                                   when r.type = 'Рабочее место'
                                       then (select count(*) from tables_table t where t.is_occupied = True)
                                   else 0
                                   END)::integer                                                 as "occupied_tables",
                       (select case
                                   when r.type = 'Рабочее место' then (select count(*) from tables_table)
                                   else 0
                                   END)::integer                                                 as "capacity_tables",
                       (select case
                                   when r.type = 'Переговорная'
                                       then (select count(*) from tables_table t where t.is_occupied = True)
                                   else 0
                                   END)::integer                                                 as "occupied_meeting",
                       (select case
                                   when r.type = 'Переговорная' then (select count(*) from tables_table)
                                   else 0
                                   END)::integer                                                 as "capacity_meeting"
                from rooms_room r"""



class Room(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    type = models.CharField(max_length=128, null=False, blank=False)  # Todo change
    floor = models.ForeignKey(Floor, related_name='rooms', null=True, blank=True, on_delete=models.CASCADE)

    @property
    def occupied(self):
        """Count of occupied tables."""
        return self.tables.filter(is_occupied=True).count()

    @property
    def capacity(self):
        """Count of tables"""
        return self.tables.count()

    @property
    def occupied_tables(self):
        """Count of occupied tables in `Рабочее место`."""
        if self.type == "Рабочее место":
            return self.occupied
        return 0

    @property
    def capacity_tables(self):
        """Count of tables in `Рабочее место`."""
        if self.type == "Рабочее место":
            return self.capacity
        return 0

    @property
    def occupied_meeting(self):
        if self.type == "Переговорная":
            return self.occupied
        return 0

    @property
    def capacity_meeting(self):
        if self.type == "Переговорная":
            return self.capacity
        return 0


# class RoomType(models.Model):  # TODO roomtypes
#     room = models.ForeignKey(Room, related_name='types', blank=False, null=False, on_delete=models.CASCADE)
#     title = models.CharField(max_length=128, blank=False, null=True)  # TODO


# class RoomImage(models.Model):
# 	file = models.ForeignKey(File, null=False, blank=False, on_delete=models.CASCADE)
# 	room = models.ForeignKey(Room, null=False, blank=False, on_delete=models.CASCADE)


# class RoomMarker(models.Model):
#     room = models.OneToOneField(Room, null=False, blank=False, on_delete=models.CASCADE)
#     icon = models.CharField(max_length=64, null=False, blank=False)
#     x = models.DecimalField(
#         max_digits=4,
#         decimal_places=2,
#         validators=[MinValueValidator(0)],
#         null=False,
#         blank=False
#     )
