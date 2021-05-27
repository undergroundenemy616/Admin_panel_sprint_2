import os
import orjson
import requests

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from booking_api_django_new.settings import PUSH_HOST, PUSH_USERNAME, PUSH_PASSWORD
from core.pagination import DefaultPagination
from core.permissions import IsAdmin
from groups.models import Group
from push_tokens.serializers_admin import AdminGroupForPushSerializer, AdminAccountForPushSerializer, \
    AdminSendPushSerializer
from users.models import Account


def check_token():
    try:
        url = PUSH_HOST + "/login"
        token = requests.post(
            url=url,
            json={
                'username': PUSH_USERNAME,
                'password': PUSH_PASSWORD
            }
        )
        token = orjson.loads(token.text)
        os.environ['PUSH_TOKEN'] = str(token.get('access_token'))
    except requests.exceptions.RequestException:
        return {"message": "Failed to get access to push service"}, 401


class AdminPushGroupView(GenericAPIView):
    serializer_class = AdminGroupForPushSerializer
    queryset = Group.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAdmin, )

    def get(self, request, *args, **kwargs):
        workspace = {'workspace': f"simpleoffice-{request.headers.get('X-WORKSPACE')}"}
        if not workspace:
            return Response('Workspace not found', status=status.HTTP_404_NOT_FOUND)
        # check_token()
        # headers = {'Authorization': 'Bearer ' + os.environ.get('PUSH_TOKEN')}
        response_from_push_service = requests.get(
            f'{PUSH_HOST}/accounts',
            params=workspace,
            # headers=headers
        )
        accounts = orjson.loads(response_from_push_service.text)
        if not accounts:
            return Response('No accounts to send push', status=status.HTTP_404_NOT_FOUND)
        ids = []
        for account in accounts[workspace['workspace']]:
            i = str(*account.values())
            if len(i) < 30:
                continue
            else:
                ids.append(i)
        if len(ids) == 0:
            return Response('No accounts to send push', status=status.HTTP_404_NOT_FOUND)
        groups_to_serialize = Group.objects.filter(accounts__in=ids).order_by('id').distinct('id')
        if not groups_to_serialize:
            return Response('No group found', status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(instance=groups_to_serialize, many=True, context=ids).data, status=status.HTTP_200_OK)


class AdminPushUserView(GenericAPIView):
    serializer_class = AdminGroupForPushSerializer
    queryset = Group.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAdmin,)

    def get(self, request, *args, **kwargs):
        workspace = {'workspace': f"simpleoffice-{request.headers.get('X-WORKSPACE')}"}
        if not workspace:
            return Response('Workspace not found', status=status.HTTP_404_NOT_FOUND)
        # check_token()
        # headers = {'Authorization': 'Bearer ' + os.environ.get('PUSH_TOKEN')}
        response_from_push_service = requests.get(
            f'{PUSH_HOST}/accounts',
            params=workspace,
            # headers=headers
        )
        accounts = orjson.loads(response_from_push_service.text)
        if not accounts:
            return Response('No accounts to send push', status=status.HTTP_404_NOT_FOUND)
        ids = []
        for account in accounts[workspace['workspace']]:
            i = str(*account.values())
            if len(i) < 30:
                continue
            else:
                ids.append(i)
        if len(ids) == 0:
            return Response([], status=status.HTTP_200_OK)
        accounts_to_serialize = Account.objects.filter(id__in=ids).prefetch_related('groups')
        if not accounts_to_serialize:
            return Response([], status=status.HTTP_200_OK)
        return Response(AdminAccountForPushSerializer(instance=accounts_to_serialize, many=True).data, status=status.HTTP_200_OK)


class AdminSendPushView(GenericAPIView):
    serializer_class = AdminSendPushSerializer
    queryset = Account.objects.all()
    permission_classes = (IsAdmin,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=request.headers)
        serializer.is_valid(raise_exception=True)
        serializer.send_message_to_push_service()
        return Response("OK", status=status.HTTP_200_OK)





