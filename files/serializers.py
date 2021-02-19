import orjson
import os
import time

import requests
from rest_framework import serializers

from booking_api_django_new.settings import (FILES_HOST, FILES_PASSWORD,
                                             FILES_USERNAME, MEDIA_ROOT,
                                             MEDIA_URL)
from files.models import File


def check_token():
    print(os.environ.get('FILES_TOKEN'))
    print(type(os.environ.get('FILES_TOKEN')))
    if os.environ.get('FILES_TOKEN') == 'None':
        print("ENTERED")
        print(FILES_HOST + "/auth")
        try:
            token = requests.post(
                url=FILES_HOST + "/auth",
                json={
                    'username': FILES_USERNAME,
                    'password': FILES_PASSWORD
                }
            )
            time.sleep(1)
            print(token.text)
            token = orjson.loads(token.text)
            print(token)
            os.environ['FILES_TOKEN'] = str(token.get('access_token'))
        except requests.exceptions.RequestException:
            return {"message": "Failed to get access to file storage"}, 401


check_token()


def create_new_folder(local_dir):
    newpath = local_dir
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    return newpath


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


class FileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = File
        fields = ['file']
        depth = 1

    def to_representation(self, instance):
        response = dict()
        response['id'] = instance.id
        response['title'] = instance.title
        response['path'] = instance.path
        response['thumb'] = instance.thumb
        response['width'] = instance.width
        response['height'] = instance.height
        return response

    def create(self, validated_data):
        file = validated_data.pop('file')
        headers = {'Authorization': 'Bearer ' + os.environ.get('FILES_TOKEN')}
        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={"file": (file.name, file.file.getvalue(), file.content_type)},
                headers=headers,
                )
        except requests.exceptions.RequestException:
            return {"message": "Error occurred during file upload"}, 500
        if response.status_code != 200:
            if response.status_code == 401:
                return {"message": "Basic Auth required"}, 401
            if response.status_code == 400:
                return {"message": "Bad request"}, 400

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

