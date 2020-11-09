import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from rooms.models import Room
from files.models import File
from offices.models import Office


class TableTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='tags', blank=False, null=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    icon = models.ForeignKey(File, on_delete=models.CASCADE, blank=True, null=True)


class Table(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tables', blank=False, null=False)
    tags = models.ManyToManyField(TableTag, related_name='tables', blank=True)
    images = models.ManyToManyField('files.File', related_name='tables', blank=True)
    is_occupied = models.BooleanField(default=False)

    @property
    def current_rating(self):
        queryset = self.ratings.all().aggregate(models.Avg('rating'))
        return queryset['rating__avg']

    def set_table_occupied(self):
        self.is_occupied = True

    def set_table_free(self):
        self.is_occupied = False


class Rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, blank=False, null=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='ratings', blank=False, null=False)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        null=False,
        blank=False
    )
