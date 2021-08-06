"""Just common utils"""
from typing import Union

import orjson
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from booking_api_django_new.settings.base import BASE_DIR
from core.handlers import ResponseException
from offices.models import Office
from tables.models import Table


def get_booking_data(office: Union[Office, str]) -> dict:
    """Returning office booking data.

    Args:
        office: Office instance or primary key
    Returns:
        dict, contains:
            `occupied`: ---
            `capacity`: ---
    """
    if not isinstance(office, Office):
        try:
            office = Office.objects.get(pk=office)
        except Office.DoesNotExist:
            msg = 'Office does not exists'
            raise ValidationError(msg)
    data = dict()
    data['occupied'] = Table.objects.filter(Q(room__floor_office=office) & Q(is_occupied=True)).count()
    data['capacity'] = Table.objects.filter(room__floor_office=office).count()
    # data['occupied_tables'] = Table.objects.filter(room__type=)
    return data


def get_localization(request, app):
    if request.headers.get('Language'):
        language = request.headers['Language']
    else:
        language = 'ru'

    try:
        with open(BASE_DIR + f'/translations/{language}_{app}.json', encoding='utf-8') as file:
            localization = orjson.loads(file.read())
    except FileNotFoundError:
        try:
            with open(BASE_DIR + f'/translations/ru_{app}.json', encoding='utf-8') as file:
                localization = orjson.loads(file.read())
        except FileNotFoundError:
            raise ResponseException(detail=f"Missing translation file for this app")
    return localization
