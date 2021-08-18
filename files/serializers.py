import os

import orjson
import requests
from rest_framework import serializers, status
from booking_api_django_new.base_settings import (FILES_HOST, FILES_PASSWORD,
                                                  FILES_USERNAME)
from booking_api_django_new.filestorage_auth import check_token
from core.handlers import ResponseException
from files.models import File


def image_serializer(image: File):
    return {
        'id': str(image.id),
        'title': image.title,
        'path': image.path,
        'thumb': image.thumb,
    }


class BaseFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = '__all__'


class TestBaseFileSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    path = serializers.CharField()
    thumb = serializers.CharField()
    height = serializers.IntegerField()
    width = serializers.IntegerField()
    size = serializers.CharField()


class FileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    title = serializers.CharField(required=False)

    class Meta:
        model = File
        fields = ['file', 'title']
        # depth = 1

    # def to_representation(self, instance):
    #     response = dict()
    #     response['id'] = instance.id
    #     response['title'] = instance.title
    #     response['path'] = instance.path
    #     response['thumb'] = instance.thumb
    #     response['width'] = instance.width
    #     response['height'] = instance.height
    #     return response

    def create(self, validated_data):
        file = validated_data.pop('file')
        check_token()
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}
        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={"file": (file.name, file.file, file.content_type)},
                headers=headers,
                )
        except requests.exceptions.RequestException:
            raise ResponseException("Error occurred during file upload", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if response.status_code != 200:
            if response.status_code == 401:
                raise ResponseException("Problems with authorization", status_code=status.HTTP_401_UNAUTHORIZED)
            if response.status_code == 400:
                raise ResponseException("Bad request", status_code=status.HTTP_401_UNAUTHORIZED)

        response_dict = orjson.loads(response.text)
        file_attrs = {
            "path": FILES_HOST + str(response_dict.get("path")),
            "title": file.name,
            "size": file.size,
            "width": response_dict.get('width'),
            "height": response_dict.get('height')
        }
        if response_dict.get("thumb"):
            file_attrs['thumb'] = FILES_HOST + str(response_dict.get("thumb"))
        file_storage_object = File(**file_attrs)
        file_storage_object.save()
        return file_storage_object

