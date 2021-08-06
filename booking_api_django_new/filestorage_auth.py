import os
import orjson
import requests

from booking_api_django_new.settings.base import FILES_HOST, FILES_USERNAME, FILES_PASSWORD


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
