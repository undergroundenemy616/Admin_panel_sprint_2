import os
import random
import time

import ipinfo
from django.contrib.auth.password_validation import validate_password
from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from booking_api_django_new.settings import DEBUG
from files.models import File
from files.serializers import BaseFileSerializer
from floors.models import Floor
from groups.models import Group
from mail import send_html_email_message
from offices.models import Office, OfficeZone
from rooms.models import Room
from users.models import Account, User, AppEntrances, OfficePanelRelation


class SwaggerAccountParametr(serializers.Serializer):
    id = serializers.UUIDField(required=False)


class SwaggerAccountListParametr(serializers.Serializer):
    account_type = serializers.CharField(required=False, max_length=20)
    include_not_activated = serializers.CharField(required=False, max_length=5)
    access_group = serializers.CharField(required=False, max_length=36)


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
        # read_only_fields = fields

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


class AccountSerializerLite(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    phone_number = serializers.CharField()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def to_representation(self, instance):
        response = super(AccountSerializerLite, self).to_representation(instance)
        response['phone_number'] = instance.user.phone_number if instance.user.phone_number else instance.phone_number
        return response


class TestAccountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    description = serializers.CharField()
    gender = serializers.CharField()
    city = serializers.IntegerField()
    region_integer = serializers.IntegerField()
    district_integer = serializers.IntegerField()
    region_string = serializers.CharField()
    district_string = serializers.CharField()
    account_type = serializers.CharField()
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True)

    def to_representation(self, instance):
        response = super(TestAccountSerializer, self).to_representation(instance)
        # response = {}
        # response['id'] = instance.id,
        # response['user'] = instance.user.id,
        # response['description'] = instance.description,
        # response['gender'] = instance.gender,
        # response['city'] = instance.city,
        # response['region_integer'] = instance.region_integer,
        # response['district_integer'] = instance.district_integer,
        # response['region_string'] = instance.region_integer,
        # response['district_string'] = instance.district_string,
        # response['account_type'] = instance.account_type,
        # response['groups'] = instance.groups.all(),
        response['is_active'] = instance.user.is_active
        response['phone_number'] = instance.user.phone_number if instance.user.phone_number else instance.phone_number
        response['firstname'] = instance.first_name
        response['lastname'] = instance.last_name
        response['middlename'] = instance.middle_name
        response['birthday'] = instance.birth_date
        response['email'] = instance.user.email if instance.user.email else instance.email
        if instance.photo:
            response['photo'] = BaseFileSerializer(instance=instance.photo).data
        response['has_cp_access'] = True if instance.user.email else False
        return response


class AccountListGetSerializer(serializers.Serializer):
    account_type = serializers.CharField(required=False, max_length=20)
    include_not_activated = serializers.CharField(required=False, max_length=5)
    access_group = serializers.CharField(required=False, max_length=36)


class LoginOrRegisterSerializer(serializers.Serializer):
    """Log in through phone"""
    phone = serializers.CharField(required=True, min_length=11, max_length=12)
    code = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User

    def save(self, **kwargs):
        pass

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class RegisterUserFromAPSerializer(serializers.Serializer):
    city = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    firstname = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    lastname = serializers.CharField(required=False, allow_blank=True)
    middlename = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField()

    def save(self, **kwargs):
        user, created = User.objects.get_or_create(phone_number=self.data['phone_number'])
        if not created:
            raise ValidationError(detail={'message': 'User already exist', 'code': '400'})
        email = None if self.data.get('email') == "" else self.data.get('email')
        account = Account.objects.create(user=user, city=self.data.get('city'), description=self.data.get('description'),
                                         email=email, first_name=self.data.get('firstname'),
                                         gender=self.data.get('gender'), last_name=self.data.get('lastname'),
                                         middle_name=self.data.get('middlename'))
        user_group = Group.objects.get(access=4, is_deletable=False, title='Посетитель')
        if not user_group:
            user_group = Group.objects.get(access=4, is_deletable=False, title='Guests')
        user.is_active = True
        user.save(update_fields=['is_active'])
        account.groups.add(user_group)
        return account


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
    phone_number = serializers.CharField(required=False)

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
        group = Group.objects.filter(title='Администратор', is_deletable=False).first()
        if not group:
            group = Group.objects.filter(title='Administrator', is_deletable=False).first()
        if not group:
            raise ValidationError('Unable to find admin group')
        email = validated_data.get('email')
        host_domain = os.environ.get('ADMIN_HOST', default='Please write ADMIN_HOST')
        is_exists = User.objects.filter(email=email).exists()
        if is_exists:
            raise ValidationError('User already exist')
        phone_number = validated_data.get('phone_number')
        if phone_number:
            if Account.objects.filter(phone_number=phone_number).exists():
                raise ValidationError(detail={"message": "User already exist"}, code=400)
        instance = User(email=email, is_active=True, is_staff=True)
        instance.set_password(password)
        instance.save()
        send_html_email_message(
            to=email,
            subject="Добро пожаловать в Simple-Office!",
            template_args={
                'host': host_domain,
                'username': email,
                'password': password
            }
        )
        account = Account.objects.get_or_create(user=instance, email=instance.email)
        account[0].groups.add(group)
        return instance


class LoginOfficePanel(serializers.Serializer):
    access_code = serializers.IntegerField(required=True)


class AccountUpdateSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name', required=False, allow_blank=True, allow_null=True)
    lastname = serializers.CharField(source='last_name', required=False, allow_blank=True, allow_null=True)
    middlename = serializers.CharField(source='middle_name', required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone_number = serializers.CharField(required=False)
    photo = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False, allow_null=True)
    city = serializers.IntegerField(required=False, allow_null=True)
    birthday = serializers.CharField(source='birth_date', required=False)
    gender = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Account
        fields = ['firstname', 'lastname', 'middlename', 'description', 'email', 'phone_number', 'photo', 'city',
                  'birthday', 'gender']

    def to_representation(self, instance):
        response = AccountSerializer(instance).data
        return response

    def validate(self, attrs):
        if attrs.get('email') == "":
            attrs['email'] = None
        return attrs


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


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=512)
    new_password = serializers.CharField(max_length=512)

    def validate(self, attrs):
        if not self.context['request'].user.check_password(attrs['old_password']):
            raise ValidationError(detail="wrong password", code=400)
        if not DEBUG:
            validate_password(attrs['new_password'], user=self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.data['new_password'])
        user.save()


class PasswordResetSerializer(serializers.Serializer):
    account = serializers.UUIDField()

    def validate(self, attrs):
        account = Account.objects.filter(pk=attrs['account']).first()
        if not account:
            raise ValidationError(detail="account not found", code=404)
        if not account.email:
            raise ValidationError(detail="User has no email specified", code=400)
        return attrs

    def save(self, **kwargs):
        account = Account.objects.get(pk=self.data['account'])
        if not account.user.email:
            account.user.email = account.email
            subject = "Добро пожаловать в Simple-Office!"
        else:
            subject = "Ваш пароль был успешно сброшен!"

        password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])
        account.user.set_password(password)

        send_html_email_message(
            to=account.email,
            subject=subject,
            template_args={
                'host': os.environ.get('ADMIN_HOST'),
                'username': account.user.email,
                'password': password
            }
        )
        account.user.save()


class EntranceCollectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppEntrances
        fields = ['device_info', ]

    def validate(self, attrs):
        account = Account.objects.get(user=self.context['request'].user)
        attrs['device_info'] = self.context['request'].data['device_info']
        attrs['user'] = account
        x_forwarded_for = self.context['request'].META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = self.context['request'].META.get('REMOTE_ADDR')
        if ip_address:
            attrs['ip_address'] = ip_address
            handler = ipinfo.getHandler(access_token="e11640aca14e4d")
            details = handler.getDetails(ip_address)
            latitude = details.all.get("latitude")
            longitude = details.all.get("longitude")
            if latitude and longitude:
                attrs["location"] = str(latitude) + " " + str(longitude)
            attrs['country'] = details.all.get("country_name") or "undefined"
            attrs['city'] = details.all.get("city") or "undefined"
        return attrs


class OfficePanelSerializer(serializers.Serializer):
    firstname = serializers.CharField(max_length=64)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all())
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), allow_null=True)

    @atomic()
    def create(self, validated_data):
        user = User.objects.create_user(is_active=True, is_staff=True)
        group = Group.objects.filter(title='Информационная панель').first()
        account = Account.objects.create(user=user, first_name=validated_data.get('firstname'), account_type='kiosk')
        if group:
            account.groups.add(group)
        else:
            group = Group.objects.create(title='Информационная панель', access=2)
            account.groups.add(group)
        instance = OfficePanelRelation.objects.create(account=account, office=validated_data.get('office'),
                                                      floor=validated_data.get('floor'),
                                                      access_code=int(time.time()))
        return instance

    @atomic()
    def update(self, instance, validated_data):
        office_panel = get_object_or_404(OfficePanelRelation, account__pk=instance.pk)
        instance.first_name = validated_data.get('firstname')
        instance.save()
        office_panel.office = validated_data.get('office')
        office_panel.floor = validated_data.get('floor')
        office_panel.save()
        # account = get_object_or_404(Account, pk=instance.account.pk)
        # account.first_name = validated_data.get('firstname')
        # account.save()
        # instance.office = validated_data.get('office')
        # instance.floor = validated_data.get('floor')
        # instance.save()
        return office_panel

    def to_representation(self, instance):
        if type(instance) == Account:
            instance = instance.office_panels
        response = TestAccountSerializer(instance.account).data
        response['office'] = {"id": instance.office.id, "title": instance.office.title}
        response['floor'] = {"id": instance.floor.id, "title": instance.floor.title}
        if instance.room:
            response['room'] = {"id": instance.room.id, "title": instance.room.title}
        response['access_code'] = instance.access_code
        return response
