from django.db import models
from files.models import File
from groups.models import Group


class Office(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    working_hours = models.CharField(max_length=128, null=True, blank=True)
    service_email = models.CharField(max_length=256, null=True, blank=True)

    @property
    def occupied(self):
        return sum(fr.occupied for fr in self.floors.all())

    @property
    def capacity(self):
        return sum(fr.capacity for fr in self.floors.all())

    @property
    def occupied_tables(self):
        return sum(fr.occupied_tables for fr in self.floors.all())

    @property
    def capacity_tables(self):
        return sum(fr.capacity_tables for fr in self.floors.all())

    @property
    def occupied_meeting(self):
        return sum(fr.occupied_meeting for fr in self.floors.all())

    @property
    def capacity_meeting(self):
        return sum(fr.capacity_meeting for fr in self.floors.all())

    @property
    def floors_number(self):
        return self.floors.count()


class OfficeImages(models.Model):
    image = models.ForeignKey(File, null=False, blank=False, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False)


class OfficeZone(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False)
    pre_defined = models.BooleanField()


class GroupWhitelist(models.Model):
    zone = models.ForeignKey(OfficeZone, on_delete=models.CASCADE, blank=False, null=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
