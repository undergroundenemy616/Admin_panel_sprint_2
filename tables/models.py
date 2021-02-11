import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from files.models import File
from offices.models import Office
from rooms.models import Room


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
    def rating(self):
        queryset = self.ratings.all().aggregate(models.Avg('rating'))
        if not queryset['rating__avg']:
            return 0
        return queryset['rating__avg']

    def set_table_occupied(self):
        self.is_occupied = True
        self.save()

    def set_table_free(self):
        self.is_occupied = False
        self.save()


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


class TableMarker(models.Model):
    table = models.OneToOneField(Table, related_name='table_marker', null=False,
                                 blank=False, on_delete=models.CASCADE)
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
