import random

from movies.factories import MovieFactory, SerialFactory, UserFactory, GenreFactory, PersonFactory
from movies.models import Person, Genre, Role


def add_users(self):
    self.stdout.write(self.style.WARNING(f'Starting create users, wait for a moment...'))
    try:
        for i in range(10):
            UserFactory()
            if i % 100 == 0:
                self.stdout.write(self.style.SUCCESS(f'{i}/1000 users created...'))
        self.stdout.write(self.style.SUCCESS(f'Users created successfully'))
    except Exception as exc:
        self.stdout.write(self.style.ERROR(f'Failed to create users, error: {exc}'))


def add_genres(self):
    self.stdout.write(self.style.WARNING(f'Starting create genres, wait for a moment...'))
    try:
        for i in range(20):
            GenreFactory()
            if i % 100 == 0:
                self.stdout.write(self.style.SUCCESS(f'{i}/20000 genres created...'))
        self.stdout.write(self.style.SUCCESS(f'Genres created successfully'))
    except Exception as exc:
        self.stdout.write(self.style.ERROR(f'Failed to create genres, error: {exc}'))


def add_persons(self):
    self.stdout.write(self.style.WARNING(f'Starting create persons, wait for a moment...'))
    try:
        persons = []
        for i in range(100):
            roles = Role.objects.all()
            person = PersonFactory.create(roles=random.choices(roles, k=random.randint(1, len(roles))))
            if i % 100 == 0:
                self.stdout.write(self.style.SUCCESS(f'{i}/1000 persons created...'))
            persons.append(person)
        self.stdout.write(self.style.SUCCESS(f'Persons created successfully'))
    except Exception as exc:
        self.stdout.write(self.style.ERROR(f'Failed to create persons, error: {exc}'))


def add_film_work(self, film_work_type):
    if film_work_type == 'Movie':
        factory = MovieFactory
        objects_count = 100
    elif film_work_type == 'Serial':
        factory = SerialFactory
        objects_count = 200
    self.stdout.write(self.style.WARNING(f'Starting create {film_work_type}, wait for a moment...'))
    try:
        actors = Person.objects.filter(roles__title='Actor')
        writers = Person.objects.filter(roles__title='Writer')
        directors = Person.objects.filter(roles__title='Director')
        genres = Genre.objects.all()[:100]
        for i in range(objects_count):
            current_actors = random.choices(actors, k=random.randint(1, 20))
            current_writers = random.choices(writers, k=random.randint(1, 3))
            current_directors = random.choices(directors, k=random.randint(1, 5))
            current_genres = random.choices(genres, k=random.randint(1, 5))
            factory.create(actors=current_actors,
                           writers=current_writers,
                           directors=current_directors,
                           genres=current_genres)
            if i % 100 == 0:
                self.stdout.write(self.style.SUCCESS(f'{i}/200000 {film_work_type} created...'))
        self.stdout.write(self.style.SUCCESS(f'{film_work_type} created successfully'))
    except Exception as exc:
        self.stdout.write(self.style.ERROR(f'Failed to create {film_work_type}, error: {exc}'))
