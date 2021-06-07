import os

import orjson
import requests
from rest_framework import serializers, status

from booking_api_django_new.settings import (FILES_HOST, FILES_PASSWORD,
                                             FILES_USERNAME)
from core.handlers import ResponseException
from files.models import File


def check_token():
    try:
        token = requests.post(
            url=FILES_HOST + "/auth",
            json={
                'username': FILES_USERNAME,
                'password': FILES_PASSWORD
            }
        )
        token = orjson.loads(token.text)
        os.environ['FILES_TOKEN'] = str(token.get('access_token'))
    except requests.exceptions.RequestException:
        return {"message": "Failed to get access to file storage"}, 401


class MobileBaseFileSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    path = serializers.CharField()
    thumb = serializers.CharField()


class MobileFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    title = serializers.CharField(required=False)

    class Meta:
        model = File
        fields = ['file', 'title']

    def create(self, validated_data):
        file = validated_data.pop('file')
        check_token()
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}
        try:
            response = requests.post(
                url=FILES_HOST.replace('"', '') + "/upload",
                files={"file": (file.name, file.file, file.content_type)},
                headers=headers,
            )
        except requests.exceptions.RequestException as e:
            raise ResponseException(f"{e}, {FILES_HOST}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if response.status_code != 200:
            if response.status_code == 401:
                raise ResponseException("Problems with authorization", status_code=status.HTTP_401_UNAUTHORIZED)
            if response.status_code == 400:
                raise ResponseException("Bad request", status_code=status.HTTP_401_UNAUTHORIZED)

        response_dict = orjson.loads(response.text)
        file_attrs = {
            "path": FILES_HOST.replace('"', '') + str(response_dict.get("path")),
            "title": file.name,
            "size": file.size,
            "width": response_dict.get('width'),
            "height": response_dict.get('height'),
        }
        if response_dict.get("thumb"):
            file_attrs['thumb'] = FILES_HOST + str(response_dict.get("thumb"))
        file_storage_object = File(**file_attrs)
        file_storage_object.save()
        return file_storage_object

