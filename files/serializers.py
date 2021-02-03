import json
import os
import uuid
from typing import Any, Dict

import PIL
import requests
from PIL import Image
from django.core.files.storage import default_storage
from rest_framework import serializers

from booking_api_django_new.settings import (FILES_HOST, FILES_PASSWORD,
                                             FILES_USERNAME, MEDIA_ROOT,
                                             MEDIA_URL)
from files.models import File
from PIL.Image import UnidentifiedImageError


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
        create_new_folder(MEDIA_ROOT)
        file = validated_data.pop('file')
        image = None
        new_name = f'{uuid.uuid4().hex + file.name}'
        path = MEDIA_ROOT + new_name
        try:
            image = Image.open(file)
            image.save(path)  # need to store with hash not with uuid
        except UnidentifiedImageError:
            with default_storage.open(new_name, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
        try:
            response = requests.post(
                url=FILES_HOST + "/upload",
                files={"file": (file.name, file.file.getvalue(), file.content_type)},
                auth=(FILES_USERNAME, FILES_PASSWORD),
                )
        except requests.exceptions.RequestException:
            return {"message": "Error occured during file upload"}, 500
        if response.status_code != 200:
            if response.status_code == 401:
                return {"message": "Basic Auth required"}, 401
            if response.status_code == 400:
                return {"message": "Bad request"}, 400

        response_dict = json.loads(response.text)
        file_attrs = {
            "path": FILES_HOST + str(response_dict.get("path")),
            "title": file.name,
            "size": file.size,
            "width": image.width if image else None,
            "height": image.height if image else None
        }
        if response_dict.get("thumb"):
            file_attrs['thumb'] = FILES_HOST + str(response_dict.get("thumb"))
        file_storage_object = File(**file_attrs)
        file_storage_object.save()
        return file_storage_object

