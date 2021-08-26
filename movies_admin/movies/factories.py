import datetime

import factory
from django.contrib.auth.hashers import make_password
from factory import LazyAttributeSequence
from factory.fuzzy import FuzzyDateTime, FuzzyChoice, FuzzyDecimal
from pytz import UTC

from .models import Genre, Person, FilmWork, User
from utils.fake import my_faker


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('id',)

    id = factory.Sequence(lambda n: my_faker.unique.uuid4())
    email = LazyAttributeSequence(lambda o, n: f'{my_faker.unique.email()}')
    date_joined = factory.Sequence(lambda n: my_faker.date_time_between(start_date='-3d'))
    username = LazyAttributeSequence(lambda o, n: f'{my_faker.unique.user_name()}')
    password = factory.LazyFunction(lambda: make_password('pi3.1415'))


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre
        django_get_or_create = ('title',)

    id = factory.Sequence(lambda n: my_faker.unique.uuid4())
    title = factory.Sequence(lambda n: 'genre{}'.format(n))
    description = factory.Sequence(lambda n: 'description{}'.format(n))


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    id = factory.Sequence(lambda n: my_faker.unique.uuid4())
    first_name = factory.Sequence(lambda n: my_faker.first_name())
    last_name = factory.Sequence(lambda n: my_faker.last_name())

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.add(role)


class FilmWorkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FilmWork

    id = factory.Sequence(lambda n: my_faker.unique.uuid4())
    type = None
    title = None
    description = None
    rating = FuzzyDecimal(0.0, 10.0)
    age_qualification = FuzzyChoice([age_qualification[0] for age_qualification in  FilmWork.AgeQualification.choices])
    file_path = None

    @factory.post_generation
    def genres(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for genre in extracted:
                self.genres.add(genre)

    @factory.post_generation
    def directors(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for director in extracted:
                self.directors.add(director)

    @factory.post_generation
    def writers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for writer in extracted:
                self.writers.add(writer)

    @factory.post_generation
    def actors(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for actor in extracted:
                self.actors.add(actor)


class MovieFactory(FilmWorkFactory):
    class Meta:
        model = FilmWork

    type = 'Movie'
    title = factory.Sequence(lambda n: 'Movie #{}'.format(n))
    description = factory.Sequence(lambda n: 'Description of movie #{}'.format(n))
    file_path = factory.Sequence(lambda n: '/movie_storage/movie{}'.format(n))


class SerialFactory(FilmWorkFactory):
    class Meta:
        model = FilmWork

    type = 'Serial'
    title = factory.Sequence(lambda n: 'Serial #{}'.format(n))
    description = factory.Sequence(lambda n: 'Description of serial #{}'.format(n))
    file_path = factory.Sequence(lambda n: '/movie_storage/serial{}'.format(n))
