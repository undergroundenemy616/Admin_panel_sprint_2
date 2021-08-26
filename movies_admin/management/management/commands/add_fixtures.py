from django.core.management.base import BaseCommand
from utils.add_fixture import add_film_work, add_persons, add_genres, add_users


class Command(BaseCommand):
    help = 'Generate testing data'

    def handle(self, *args, **options):
        add_users(self),
        add_genres(self),
        add_persons(self),
        add_film_work(self, 'Movie')
        add_film_work(self, 'Serial')
