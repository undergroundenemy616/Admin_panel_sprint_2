"""Just common utils"""
from typing import Union

from django.db.models import Q
from rest_framework.exceptions import ValidationError
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
