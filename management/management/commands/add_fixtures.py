import logging

from django.core.management.base import BaseCommand
from core.fixtures import AddFixtures
from floors.models import Floor
from groups.models import Group
from licenses.models import License
from offices.models import Office, OfficeZone
from room_types.models import RoomType
from rooms.models import Room
from tables.models import Table
from users.models import User, Account


def default_table_for_room(room):
    table = Table.objects.create(room=room, title=room.title)
    return table


class Command(BaseCommand):
    help = 'Select language for fixtures'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('__name__')
        self.error_count = 0
        self.created = []

    def add_arguments(self, parser):
        parser.add_argument('-l', '--language', type=str, help='Language', )

    def handle(self, *args, **kwargs):
        language = kwargs['language'] if kwargs['language'] else 'en'
        self.logger.warning(msg=f'Selected language: {language}')
        self.logger.warning('--------------')

        add_fixtures = AddFixtures(language)

        groups = add_fixtures.add_fixture(model=Group)

        users = add_fixtures.add_fixture(model=User)

        account = add_fixtures.add_fixture(model=Account,
                                           along_with=[{'parameter': 'user', 'values': users, 'on_value': 'email'}],
                                           bind_with=[{'parameter': 'groups', 'values': groups, 'on_value': 'title'}])

        licenses = add_fixtures.add_fixture(model=License)

        offices = add_fixtures.add_fixture(model=Office,
                                           parents={'parameter': 'license', 'values': licenses, 'not_strict': True})

        zones = add_fixtures.add_fixture(model=OfficeZone, parents={'parameter': 'office', 'values': offices},
                                         bind_with=[{'parameter': 'groups', 'values': groups, 'on_value': 'title'}])

        room_types = add_fixtures.add_fixture(model=RoomType, parents={'parameter': 'office', 'values': offices})

        floors = add_fixtures.add_fixture(model=Floor, parents={'parameter': 'office', 'values': offices})

        rooms = add_fixtures.add_fixture(model=Room, parents={'parameter': 'floor', 'values': floors},
                                         along_with=[{'parameter': 'type', 'on_value': 'title', 'values': room_types},
                                                     {'parameter': 'zone', 'on_value': 'title', 'values': zones}])

        tables = add_fixtures.add_fixture(
            model=Table, parents={'parameter': 'room', 'values': rooms, 'exclude': ['type.unified', 'type.bookable'],
                                  'exclude_value': [True, False], 'default': [default_table_for_room, None]})

        add_fixtures.print_result()

