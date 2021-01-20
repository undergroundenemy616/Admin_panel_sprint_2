from rest_framework import serializers

from push_tokens.models import PushToken
from users.models import Account


class PushMessageSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    body = serializers.CharField(required=True)
    data = serializers.DictField(required=False, default={})
    sound = serializers.CharField(required=False, default='default')
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high'], required=False, default='high')

    class Meta:
        fields = '__all__'


class PushSendSingleSerializer(serializers.ModelSerializer):
    expo = PushMessageSerializer(required=True)

    class Meta:
        model = PushToken
        fields = ['account', 'expo']


class PushSendBroadcastSerializer(serializers.ModelSerializer):
    accounts = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=True, many=True)
    expo = PushMessageSerializer(required=True)

    class Meta:
        model = PushToken
        fields = ['accounts', 'expo']


class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = '__all__'
