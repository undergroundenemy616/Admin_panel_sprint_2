import random

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.pagination import DefaultPagination
from files.models import File
from files.serializers import BaseFileSerializer
from groups.models import GUEST_ACCESS, OWNER_ACCESS, Group
from mail import send_html_email_message
from users.models import Account, User
from offices.models import OfficeZone, Office


class SwaggerAccountParametr(serializers.Serializer):
    id = serializers.UUIDField(required=False)


class SwaggerAccountListParametr(serializers.Serializer):
    search = serializers.CharField(required=False, max_length=256)
    account_type = serializers.CharField(required=False, max_length=20)
    include_not_activated = serializers.CharField(required=False, max_length=5)


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
        response['phone_number'] = instance.user.phone_number if instance.user.phone_number else instance.phone_number
        response['firstname'] = response.pop('first_name')
        response['lastname'] = response.pop('last_name')
        response['middlename'] = response.pop('middle_name')
        response['birthday'] = response.pop('birth_date')
        response['email'] = instance.user.email if instance.user.email else instance.email
        if instance.photo:
            response['photo'] = BaseFileSerializer(instance=instance.photo).data
        response['has_cp_access'] = True if instance.user.email else False
        return response


class LoginOrRegisterSerializer(serializers.Serializer):
    """Log in through phone"""
    phone = serializers.CharField(required=True, min_length=11, max_length=12)
    code = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)

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
    username = serializers.EmailField(required=True, min_length=0, max_length=128)
    password = serializers.CharField(required=True, min_length=0, max_length=128)

    def save(self, **kwargs):
        pass

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class RegisterStaffSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='email', required=True)
    host_domain = serializers.CharField(required=False, default='')

    class Meta:
        model = User
        fields = '__all__'

    def to_representation(self, instance):
        response = UserSerializer(instance).data
        response['account'] = instance.account.id
        return response

    def create(self, validated_data):
        validated_data.setdefault('is_staff', True)
        password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])
        group = Group.objects.filter(access=2, is_deletable=False).first()
        if not group:
            raise ValidationError('Unable to find admin group')
        email = validated_data.get('email')
        host_domain = validated_data.pop('host_domain', '')
        is_exists = User.objects.filter(email=email).exists()
        if is_exists:
            raise ValidationError('Admin already exists.')
        instance = super(RegisterStaffSerializer, self).create(validated_data)
        instance.set_password(password)
        instance.save()
        send_html_email_message(
            to=email,
            subject="Добро пожаловать в Газпром!",
            template_args={
                'host': host_domain,
                'username': email,
                'password': password
            }
        )
        account = Account.objects.get_or_create(user=instance, email=instance.email)
        account[0].groups.add(group)
        return instance


class AccountUpdateSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name', required=False)
    lastname = serializers.CharField(source='last_name', required=False)
    middlename = serializers.CharField(source='middle_name', required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    photo = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, allow_null=True)
    city = serializers.IntegerField(required=False, allow_null=True)
    birthday = serializers.CharField(source='birth_date', required=False)
    gender = serializers.CharField(required=False)

    class Meta:
        model = Account
        fields = ['firstname', 'lastname', 'middlename', 'description', 'email', 'phone_number', 'photo', 'city',
                  'birthday', 'gender']

    def to_representation(self, instance):
        response = AccountSerializer(instance).data
        return response


def user_access_serializer(group_id):
    office_zones = OfficeZone.objects.filter(groups=group_id)

    if not office_zones:
        return []

    response = []

    for zone in office_zones:
        item = {
            'id': zone.office.id,
            'title': zone.office.title,
            'description': zone.office.description,
            'zones': []
        }
        response.append(item)

    response = list({item['id']: item for item in response}.values())

    for item in response:
        filtered_zones = office_zones.filter(office=item['id'])
        for filtered_zone in filtered_zones:
            item['zones'].append({
                'id': str(filtered_zone.id),
                'title': filtered_zone.title
            })

    return response

