import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FilmWork(BaseModel):
    class AgeQualification(models.TextChoices):
        A = 0
        B = 6
        C = 12
        D = 16
        F = 18

    class FilmWorkType(models.TextChoices):
        movie = 'Movie'
        serial = 'Serial'

    title = models.TextField(_('название'), null=False, blank=True)
    description = models.TextField(_('описание'), null=True, blank=True)
    creation_date = models.DateField(_('дата создания'), null=True)
    age_qualification = models.IntegerField(_('возрастное ограничение'), choices=AgeQualification.choices)
    type = models.TextField(_('тип'), choices=FilmWorkType.choices)
    directors = models.ManyToManyField('Person', related_name='director')
    rating = models.DecimalField(_('рейтинг'), max_digits=3, decimal_places=1, null=True, blank=True)
    actors = models.ManyToManyField('Person', related_name='actor')
    writers = models.ManyToManyField('Person', related_name='writer')
    genres = models.ManyToManyField('Genre')
    file_path = models.TextField(_('ссылка'))

    class Meta:
        verbose_name = _('кинопроизведение')
        verbose_name_plural = _('кинопроизведения')

    def __str__(self):
        return self.title


class Role(BaseModel):
    class PersonRole(models.TextChoices):
        actor = 'Actor'
        writer = 'Writer'
        director = 'Director'

    title = models.CharField(_('название'), max_length=8, choices=PersonRole.choices)

    class Meta:
        verbose_name = _('роль')
        verbose_name_plural = _('роли')

    def __str__(self):
        return self.title


class Person(BaseModel):
    first_name = models.TextField(_('имя'), null=False, blank=True)
    last_name = models.TextField(_('фамилия'), null=True, blank=True)
    roles = models.ManyToManyField(Role, related_name="person")

    class Meta:
        verbose_name = _('персона')
        verbose_name_plural = _('персоны')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Genre(BaseModel):
    title = models.TextField(_('название'), null=False, blank=True, unique=True)
    description = models.TextField(_('описание'), null=True)

    class Meta:
        verbose_name = _('жанр')
        verbose_name_plural = _('жанры')

    def __str__(self):
        return self.title
