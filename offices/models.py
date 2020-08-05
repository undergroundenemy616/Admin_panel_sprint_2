from django.db import models
from files.models import Files
from groups.models import Group


class Office(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	description = models.CharField(max_length=256, null=True, blank=True)
	working_hours = models.CharField(max_length=128, null=True, blank=True)
	service_email = models.CharField(max_length=256, null=True, blank=True)


class OfficeImages(models.Model):
	image = models.ForeignKey(Files, null=False, blank=False, on_delete=models.CASCADE)
	office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False)


class OfficeZone(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False)
	pre_defined = models.BooleanField()


class GroupWhitelist(models.Model):
	group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
	zone = models.ForeignKey(OfficeZone, on_delete=models.CASCADE, blank=False, null=False)
