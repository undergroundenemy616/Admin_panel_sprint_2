import requests
from rest_framework import serializers

from booking_api_django_new.settings import PUSH_HOST
from groups.models import Group
from users.models import Account


class AdminGroupForPushSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    title = serializers.CharField(required=False)

    class Meta:
        model = Group
        fields = ['id', 'title']

    def to_representation(self, instance):
        response = super(AdminGroupForPushSerializer, self).to_representation(instance)
        response['users'] = [user.id for user in instance.accounts.all() if str(user.id) in self.context]
        return response


class AdminAccountForPushSerializer(serializers.Serializer):
    phone_number = serializers.CharField(allow_null=True, allow_blank=True)
    id = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    first_name = serializers.CharField(allow_null=True, allow_blank=True)
    last_name = serializers.CharField(allow_null=True, allow_blank=True)
    middle_name = serializers.CharField(allow_null=True, allow_blank=True)

    def to_representation(self, instance):
        response = super(AdminAccountForPushSerializer, self).to_representation(instance)
        response['phone_number'] = instance.user.phone_number
        response['email'] = instance.user.email
        response['groups_id'] = [group.id for group in instance.groups.all()]
        return response


class AdminSendPushSerializer(serializers.Serializer):
    accounts = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Account.objects.all()))
    expo = serializers.DictField(child=serializers.CharField(), required=True)

    def send_message_to_push_service(self):
        request = self.context
        workspace = f"simpleoffice-{request.get('X-WORKSPACE')}"
        # check_token()
        # headers = {'Authorization': 'Bearer ' + os.environ.get('PUSH_TOKEN')}
        # response_from_push_service = requests.post(
        #     f'{PUSH_HOST}/send_broadcast',
        #     params=workspace,
        #     # headers=headers
        # )
        json_to_push_serivice = {
            'accounts': [str(item) for item in self.data.get('accounts')],
            'app': workspace,
            'expo': self.data.get('expo')
        }
        response = requests.post(
            f"{PUSH_HOST}/send_broadcast",
            json=json_to_push_serivice,
            headers={'content-type': 'application/json'}
        )
        return response
