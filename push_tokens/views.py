import os

import requests
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.response import Response

from booking_api_django_new.settings.base import PUSH_HOST
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticatedOnPost
from push_tokens.models import PushToken
from push_tokens.serializers import (PushSendBroadcastSerializer,
                                     PushSendSingleSerializer,
                                     PushTokenSerializer)
from users.models import Account


class PushTokenView(ListModelMixin,
                    CreateModelMixin,
                    GenericAPIView):
    serializer_class = PushTokenSerializer
    queryset = PushToken.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAdmin, IsAuthenticatedOnPost)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class PushTokenSendSingleView(GenericAPIView):
    serializer_class = PushSendSingleSerializer
    queryset = PushToken.objects.all()
    permission_classes = (IsAdmin,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = get_object_or_404(Account, id=serializer.data.get('account'))
        data_for_expo = serializer.data.get('expo')
        push_group = request.tenant.schema_name if os.environ.get('ALLOW_TENANT') else os.environ.get("PUSH_GROUP")

        expo_data = {
            "account": str(account.id),
            "app": push_group,
            "expo": {
                "title": data_for_expo.get('title'),
                "body": data_for_expo.get('body'),
                "data": data_for_expo.get('data')
            }
        }

        response = requests.post(
            PUSH_HOST + "/send_push",
            json=expo_data,
            headers={'content-type': 'application/json'}
        )

        if not response:
            return Response(
                {
                    "type": "error",
                    "message": f"Unable to find tokens for account {account.id}"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response("Push notification sent", status=status.HTTP_200_OK)


class PushTokenSendBroadcastView(PushTokenSendSingleView):
    serializer_class = PushSendBroadcastSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        accounts = [get_object_or_404(Account, id=account_id) for account_id in serializer.data.get('accounts')]
        data_for_expo = serializer.data.get('expo')
        push_group = request.tenant.schema_name if os.environ.get('ALLOW_TENANT') else os.environ.get("PUSH_GROUP")
        responses = {}

        for account in accounts:
            expo_data = {
                "account": str(account.id),
                "app": push_group,
                "expo": {
                    "title": data_for_expo.get('title'),
                    "body": data_for_expo.get('body'),
                    "data": data_for_expo.get('data')
                }
            }

            response = requests.post(
                PUSH_HOST + "/send_push",
                json=expo_data,
                headers={'content-type': 'application/json'}
            )

            phone_number = account.phone_number if account.phone_number else account.user.phone_number

            if not response:
                responses[phone_number] = "Unable to send push notification to this account"
            else:
                responses[phone_number] = "Push notification sent"

        if not responses:
            return Response(
                {
                    "type": "error",
                    "message": f"Unable to find tokens for accounts"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(responses, status=status.HTTP_200_OK)
