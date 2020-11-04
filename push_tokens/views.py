from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, \
    ListModelMixin
from rest_framework.permissions import AllowAny
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAuthenticated, IsAuthenticatedOnPost
from push_tokens.models import PushToken
from push_tokens.send_interface import send_push_message
from push_tokens.serializers import PushTokenSerializer, PushSendSingleSerializer, PushSendBroadcastSerializer
from tables.models import Table, TableTag
from tables.serializers import TableSerializer, TableTagSerializer, CreateTableSerializer
from rest_framework.viewsets import ModelViewSet

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
        expo_data = serializer.data.get('expo')
        response = {}
        for token in [push_object.token for push_object in account.push_tokens.all()]:
            response[token] = {}
            response[token]['type'], response[token]['message'] = send_push_message(token, expo_data)
        if not response:
            return Response(
                {
                    "type": "error",
                    "message": f"Unable to find tokens for account {account.id}"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(response, status=status.HTTP_200_OK)


class PushTokenSendBroadcastView(PushTokenSendSingleView):
    serializer_class = PushSendBroadcastSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        accounts = [get_object_or_404(Account, id=account_id) for account_id in serializer.data.get('accounts')]
        expo_data = serializer.data.get('expo')
        response = {}
        for account in accounts:
            account_response = {}
            for token in [push_object.token for push_object in account.push_tokens.all()]:
                account_response[token] = {}
                account_response[token]['type'], response[token]['message'] = send_push_message(token, expo_data)
            response[account.id] = account_response or {
                "type": "error",
                "message": f"Unable to find tokens for account {account.id}"
            }
        if not response:
            return Response(
                {
                    "type": "error",
                    "message": f"Unable to find tokens for accounts"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(response, status=status.HTTP_200_OK)
