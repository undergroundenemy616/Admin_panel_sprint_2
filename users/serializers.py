from rest_framework import serializers
from users.models import User, Account


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = 'id, phone_number, password, email'


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class LoginOrRegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True, min_length=11, max_length=12)
    sms_code = serializers.IntegerField(required=False, min_value=4, max_value=4)

    class Meta:
        model = User

    def save(self, **kwargs):
        pass

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
