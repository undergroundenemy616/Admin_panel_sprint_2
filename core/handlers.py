from django.utils.encoding import force_text
from rest_framework import status
from rest_framework.exceptions import APIException


class ResponseException(APIException):
    def __init__(self, detail='Bad request', status_code=status.HTTP_400_BAD_REQUEST):
        self.status_code = status_code
        self.default_detail = detail
        self.detail = {'message': force_text(self.default_detail)}
