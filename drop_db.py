"""Drop all tables in current DB."""
import os

os.environ.setdefault('BRANCH', 'crowiant')

from django.core.exceptions import ImproperlyConfigured
from booking_api_django_new.settings import DATABASES
from django.db import connection

QUERY = """DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;"""

GRANT = """GRANT ALL ON SCHEMA public TO {0};
        GRANT ALL ON SCHEMA public TO {1};"""


def drop_database(cursor):
    """Execute sql-query to database."""
    try:
        cursor.execute(QUERY)
        cursor.execute(GRANT.format(DATABASES['default'].get('USER'), 'public'))
    except Exception as error:
        print(error)
        return False
    return True


def main():
    """Start"""
    database = DATABASES.get('default', None)
    if database is None:
        msg = 'Are you defined the default key in `DATABASES`?'
        raise ValueError(msg)

    drop_database(connection.cursor())


if __name__ == '__main__':
    try:
        word = input('Enter `yes` for drop all database, or any character for exit\n\n')
        if word == 'yes':
            main()
            print('DATABASE WAS DROP')
    except ImproperlyConfigured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings')
        print('Setting environment `DJANGO_SETTINGS_MODULE`')
        main()
        print('DATABASE WAS DROP')
