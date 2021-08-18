import os
import uuid

import requests
from django.core.validators import MinValueValidator
from django.db import models
from rest_framework import status

from booking_api_django_new.filestorage_auth import check_token
from booking_api_django_new.base_settings import FILES_HOST
from core.handlers import ResponseException


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    path = models.CharField(max_length=256, null=False, blank=False)
    thumb = models.CharField(max_length=256, null=True, blank=True)
    size = models.CharField(max_length=10, null=True, blank=False)
    width = models.IntegerField(null=True, blank=False, validators=[MinValueValidator(0)], default=0)
    height = models.IntegerField(null=True, blank=False, validators=[MinValueValidator(0)], default=0)

    def delete(self, using=None, keep_parents=False):
        check_token()
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}
        try:
            response = requests.delete(
                url=self.path.replace('/files/', '/uploads/').replace('"', ''),
                headers=headers,
            )
        except requests.exceptions.RequestException as e:
            raise ResponseException(f"{e}, {FILES_HOST}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if response.status_code != 200:
            if response.status_code == 401:
                raise ResponseException("Problems with authorization", status_code=status.HTTP_401_UNAUTHORIZED)
            if response.status_code == 400:
                raise ResponseException("Bad request", status_code=status.HTTP_401_UNAUTHORIZED)
        if self.thumb:
            try:
                response = requests.delete(
                    url=self.thumb.replace('/files/', '/uploads/').replace('"', ''),
                    headers=headers,
                )
            except requests.exceptions.RequestException as e:
                raise ResponseException(f"{e}, {FILES_HOST}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if response.status_code != 200:
                if response.status_code == 401:
                    raise ResponseException("Problems with authorization", status_code=status.HTTP_401_UNAUTHORIZED)
                if response.status_code == 400:
                    raise ResponseException("Bad request", status_code=status.HTTP_401_UNAUTHORIZED)

        super(self.__class__, self).delete(using, keep_parents)
