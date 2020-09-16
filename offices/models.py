from django.db import models
from django.db.models import Sum
from files.models import File
from groups.models import Group


class Office(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    working_hours = models.CharField(max_length=128, null=True, blank=True)
    service_email = models.CharField(max_length=256, null=True, blank=True)
    images = models.ManyToManyField(File, related_name='offices')

    @property
    def occupied(self):
        return self.objects.all().aggregate(Sum('occupied'))

    @property
    def capacity(self):
        return self.objects.all().aggregate(Sum('capacity'))

    @property
    def occupied_tables(self):
        return self.objects.all().aggregate(Sum('occupied_tables'))

    @property
    def capacity_tables(self):
        return self.objects.all().aggregate(Sum('capacity_tables'))

    @property
    def occupied_meeting(self):
        return self.objects.all().aggregate(Sum('occupied_meeting'))

    @property
    def capacity_meeting(self):
        return self.objects.all().aggregate(Sum('capacity_meeting'))

    @property
    def floors_number(self):
        return self.floors.count()


class OfficeZone(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False)
    pre_defined = models.BooleanField()


class GroupWhitelist(models.Model):
    zone = models.ForeignKey(OfficeZone, on_delete=models.CASCADE, blank=False, null=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
