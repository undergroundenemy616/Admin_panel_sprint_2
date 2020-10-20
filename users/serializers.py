from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from groups.models import Group, CLIENT_ACCESS, OWNER_ACCESS
from users.models import User, Account


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            'password': {'write_only': True},
        }


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'password', 'email')


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

    def to_representation(self, instance):
        instance: Account
        response = super(AccountSerializer, self).to_representation(instance)
        response['email'] = instance.user.email
        return response


class LoginOrRegisterSerializer(serializers.Serializer):
    """Log in through phone"""
    phone_number = serializers.CharField(required=True, min_length=11, max_length=12)
    sms_code = serializers.IntegerField(required=False)

    class Meta:
        model = User

    def save(self, **kwargs):
        pass

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class LoginOrRegisterStaffSerializer(serializers.Serializer):
    """Log in through email and password"""
    email = serializers.EmailField(required=True, min_length=0, max_length=128)
    password = serializers.CharField(required=True, min_length=0, max_length=128)

    def save(self, **kwargs):
        pass

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class RegisterStaffSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='email', required=True)
    password = serializers.CharField(required=True, write_only=True)
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), required=True)  # fixme change to group

    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        validated_data.setdefault('is_staff', True)
        password = validated_data.pop('password')
        group = validated_data.get('groups')
        is_exists = User.objects.filter(email=validated_data.get('email')).exists()
        if is_exists:
            raise ValidationError('Admin already exists.')
        if not (OWNER_ACCESS < group.access < CLIENT_ACCESS):
            raise ValidationError(f'Group access must be in range from {OWNER_ACCESS} to {CLIENT_ACCESS}')
        instance = super(RegisterStaffSerializer, self).create(validated_data)
        instance.set_password(password)
        instance.save()
        return instance
