from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from rooms.models import Room
from users.models import Account
from files.models import Files
from offices.models import Office


class TableTag(models.Model):
	office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='tags', blank=False, null=False)
	title = models.CharField(max_length=256, null=False, blank=False)
	icon = models.ForeignKey(
		Files,
		on_delete=models.CASCADE,
		blank=True,
		null=True
	)


class Table(models.Model):
	title = models.CharField(max_length=256, null=False, blank=False)
	description = models.CharField(max_length=256, null=True, blank=True)
	room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tables', blank=False, null=False)
	status = models.CharField(max_length=64, null=False, blank=False, default='not_activated')
	tags = models.ManyToManyField(TableTag, null=True, blank=True)
	is_occupied = models.BooleanField(null=False, blank=False, default=False)

	@property
	def current_rating(self):
		queryset = self.ratings.all().aggregate(models.Avg('rating'))
		return queryset["rating__avg"]


class Rating(models.Model):
	account = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False)
	table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='ratings', blank=False, null=False)
	rating = models.DecimalField(
		max_digits=3,
		decimal_places=2,
		validators=[MinValueValidator(0), MaxValueValidator(5)],
		null=False,
		blank=False
	)
