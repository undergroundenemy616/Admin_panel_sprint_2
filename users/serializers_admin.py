import os
import random
import time

import phonenumbers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.db import IntegrityError
from django.db.models import Q
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as ValErr
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from core.utils import get_localization
from rooms.models import Room
from users.tasks import send_register_email

from booking_api_django_new.settings import DEBUG, ADMIN_HOST, BASE_DIR
from bookings.models import Booking
from core.handlers import ResponseException
from files.serializers_admin import AdminFileSerializer
from floors.models import Floor
from groups.models import Group
from mail import send_html_email_message
from offices.models import Office
from users.models import Account, OfficePanelRelation, User


class AdminOfficePanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        exclude = ('updated_at', 'photo')

    def to_representation(self, instance):
        response = super(AdminOfficePanelSerializer, self).to_representation(instance)
        response['is_active'] = instance.user.is_active
        response['has_cp_access'] = True if instance.user.email else False
        response['office'] = {
            "id": instance.office_panels.office.id,
            "title": instance.office_panels.office.title
        }
        response['floor'] = {
            "id": instance.office_panels.floor.id,
            "title": instance.office_panels.floor.title
        }
        response['access_code'] = instance.office_panels.access_code
        response['room'] = {'id': instance.office_panels.room_id,
                            'title': instance.office_panels.room.title} if instance.office_panels.room else None
        return response


class AdminOfficePanelCreateUpdateSerializer(serializers.Serializer):
    firstname = serializers.CharField(max_length=64)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all())
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())

    @atomic()
    def create(self, validated_data):
        user = User.objects.create_user(is_active=True, is_staff=True)
        group = Group.objects.filter(title='Информационная панель', is_deletable=False).first()
        account = Account.objects.create(user=user, first_name=validated_data.get('firstname'), account_type='kiosk')
        if group:
            account.groups.add(group)
        else:
            try:
                group = Group.objects.create(title='Информационная панель', access=2, is_deletable=False)
            except IntegrityError:
                raise ResponseException("Problem's with groups. Contact administrator")

            account.groups.add(group)
        instance = OfficePanelRelation.objects.create(account=account, office=validated_data.get('office'),
                                                      floor=validated_data.get('floor'),
                                                      room=validated_data.get('room'),
                                                      access_code=int(time.time()))
        return instance

    @atomic()
    def update(self, instance, validated_data):
        office_panel = get_object_or_404(OfficePanelRelation, account__pk=instance.pk)
        instance.first_name = validated_data.get('firstname')
        instance.save()
        office_panel.office = validated_data.get('office')
        office_panel.floor = validated_data.get('floor')
        office_panel.room = validated_data.get('room')
        office_panel.save()
        return office_panel

    def to_representation(self, instance):
        if type(instance) == Account:
            instance = instance.office_panels
        response = AdminOfficePanelSerializer(instance.account).data
        return response


class AdminUserSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    photo = AdminFileSerializer()

    class Meta:
        model = Account
        fields = '__all__'

    def to_representation(self, instance):
        response = super(AdminUserSerializer, self).to_representation(instance)
        if not response['phone_number']:
            response['phone_number'] = instance.user.phone_number
        if not response['email']:
            response['email'] = instance.user.email
        response['has_cp_access'] = True if instance.user.email else False
        try:
            if self.context['request'].query_params.get('date_from') and self.context['request'].query_params.get('date_to')\
                    and self.context['request'].query_params.get('unified'):
                if Booking.objects.is_user_overflowed(account=instance,
                                                      date_from=self.context['request'].query_params.get('date_from'),
                                                      date_to=self.context['request'].query_params.get('date_to'),
                                                      room_type=self.context['request'].query_params.get('unified')=='true'):
                    response['is_available'] = False
                else:
                    response['is_available'] = True
        except KeyError:
            pass
        return response
    
    @atomic()
    def update(self, instance, validated_data):
        if validated_data.get('photo') != str(instance.account.photo_id):
            try:
                instance.account.photo.delete()
                instance.account.photo = None
            except AttributeError:
                pass
        
        return super(AdminUserSerializer, self).update(instance=instance, validated_data=validated_data)


class AdminUserCreateUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField()
    email = serializers.EmailField(allow_blank=True, allow_null=True)

    class Meta:
        model = Account
        exclude = ['user']

    def validate(self, attrs):
        if not attrs.get('email'):
            attrs['email'] = None
        try:
            attrs['phone_number'] = User.normalize_phone(attrs['phone_number'])
        except ValueError as e:
            raise ResponseException(e)
        if not self.instance:
            if User.objects.filter(phone_number=attrs['phone_number']).exists():
                raise ResponseException("User with this phone already exists")
            if attrs.get('email') and User.objects.filter(email=attrs['email']):
                raise ResponseException("User with this email already exists")
        else:
            if attrs.get('email') and self.instance.user.email != attrs['email'] and User.objects.filter(email=attrs['email']):
                raise ResponseException("User with this email already exists")
            if self.instance.user.phone_number != attrs['phone_number'] and User.objects.filter(phone_number=attrs['phone_number']):
                raise ResponseException("User with this phone already exists")
        return attrs

    @atomic()
    def create(self, validated_data):
        user = User.objects.create(phone_number=validated_data.pop('phone_number'), is_active=True,
                                   email=validated_data.pop('email'))
        validated_data['user'] = user
        password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])

        localization = get_localization(self.context['request'], 'users')

        user.set_password(password)
        user.save()

        send_register_email.delay(email=user.email, subject=localization['greetings'],
                                  args={"username": user.email, "password": password},
                                  template=localization['greetings_template'])
        instance = super(AdminUserCreateUpdateSerializer, self).create(validated_data)
        try:
            user_group = Group.objects.get(access=4, is_deletable=False, title='Посетитель')
        except IntegrityError:
            raise ResponseException("Problem's with groups. Contact administrator")
        instance.groups.add(user_group)
        return instance

    @atomic()
    def update(self, instance, validated_data):
        if validated_data.get('phone_number'):
            instance.user.phone_number = validated_data['phone_number']
            instance.user.save()
        if validated_data.get('email'):
            instance.user.email = validated_data['email']
            instance.user.save()
        return super(AdminUserCreateUpdateSerializer, self).update(instance, validated_data)

    def to_representation(self, instance):
        return AdminUserSerializer(instance=instance).data


class AdminCreateOperatorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    phone_number = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        model = Account
        fields = '__all__'

    def validate(self, attrs):
        if User.objects.filter(Q(phone_number=attrs['phone_number']) | Q(email=attrs['email'])):
            raise ValidationError(detail={"message": 'User with this credentials already exists'}, code=400)
        try:
            attrs['phone_number'] = User.normalize_phone(attrs['phone_number'])
        except ValueError as e:
            raise ResponseException(e)
        return attrs

    @atomic()
    def create(self, validated_data):

        password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])
        user = User.objects.create(is_active=True, is_staff=True, email=validated_data.pop('email'),
                                   phone_number=validated_data.pop('phone_number'))
        user.set_password(password)
        user.save()
        validated_data['user'] = user
        instance = super(AdminCreateOperatorSerializer, self).create(validated_data)

        group = Group.objects.filter(title='Администратор', is_deletable=False).first()
        if not group:
            raise ValidationError(detail={"message": 'Unable to find admin group'}, code=400)
        instance.groups.add(group)

        email = validated_data.get('email')
        if not ADMIN_HOST:
            raise ValidationError(detail={"message": "ADMIN_HOST not specified"}, code=400)

        if self.context['request'].headers.get('Language', None) == 'ru':
            send_html_email_message(
                to=email,
                subject="Добро пожаловать в Simple-Office!",
                template_args={
                    'host': ADMIN_HOST,
                    'username': email,
                    'password': password
                },
                language='ru'
            )
        else:
            send_html_email_message(
                to=email,
                subject="Welcome to Simple-Office!",
                template_args={
                    'host': ADMIN_HOST,
                    'username': email,
                    'password': password
                },
                language='en'
            )
        return instance

    def to_representation(self, instance):
        return AdminUserSerializer(instance=instance).data


class AdminServiceEmailViewValidatorSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    title = serializers.CharField(allow_blank=True)
    body = serializers.CharField(allow_blank=True)


class AdminPasswordResetSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())

    def validate(self, attrs):
        account = attrs.get('user')
        if not account.email and not account.user.email:
            raise ValidationError(detail="User has no email specified", code=400)
        return attrs

    @atomic()
    def save(self, **kwargs):
        account = Account.objects.get(pk=self.data['user'])
        if self.context['request'].headers.get('Language', None) == 'ru':
            if not account.user.email:
                account.user.email = account.email
                subject = "Добро пожаловать в Simple-Office!"
            else:
                subject = "Ваш пароль был успешно сброшен!"
        else:
            if not account.user.email:
                account.user.email = account.email
                subject = "Welcome to Simple-Office!"
            else:
                subject = "Your password was successfully reset"

        password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])
        account.user.set_password(password)

        send_html_email_message(
            to=account.user.email,
            subject=subject,
            template_args={
                'host': os.environ.get('ADMIN_HOST'),
                'username': account.user.email,
                'password': password
            },
            language=self.context['request'].headers.get('Language', 'ru')
        )
        account.user.save()


class AdminPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=512)
    new_password = serializers.CharField(max_length=512)

    def validate(self, attrs):

        if attrs['old_password'] == attrs['new_password']:
            raise ValidationError(detail="Old and new password can't match")

        if not self.context['request'].user.check_password(attrs['old_password']):
            raise ValidationError(detail="wrong password", code=400)
        if not DEBUG:
            validate_password(attrs['new_password'], user=self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.data['new_password'])
        user.save()


class AdminLoginSerializer(serializers.Serializer):

    username = serializers.EmailField(required=True, min_length=0, max_length=128)
    password = serializers.CharField(required=True, min_length=0, max_length=128)

    def auth(self):
        """Returns tuple of (user, None) if authentication credentials correct, otherwise returns (None, message)."""
        try:
            user = User.objects.get(email=self.validated_data.get('username'), is_staff=True, password__isnull=False)
        except (User.DoesNotExist, KeyError, TypeError):
            return None, 'Incorrect email or password'
        is_correct = user.check_password(self.validated_data.get('password'))
        if not is_correct:
            return None, 'Incorrect email or password'

        if not user.is_staff or not user.is_active:
            return None, 'User is not a staff or has been blocked.'

        return user, None


class AdminPromotionDemotionSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())

    def change_status(self):
        account = self.validated_data.get('account')
        if account.user.is_staff:
            account.user.password = None
            account.user.is_staff = False
            account.user.save()
            for group in account.groups.all():
                if group.access == 2:
                    account.groups.remove(group)
            return 'Demoted'

        account.user.is_staff = True
        password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])
        group = Group.objects.filter(access=2, is_deletable=False).first()
        account.user.set_password(password)
        account.user.save()
        account.groups.add(group)
        send_html_email_message(
            to=account.email,
            subject="Добро пожаловать в Simple-Office!",
            template_args={
                'host': os.environ.get('ADMIN_HOST'),
                'username': account.user.email,
                'password': password
            }
        )
        return 'Promoted'

    def validate(self, attrs):
        if not attrs['account'].email:
            raise ValidationError(detail='User has no email specified', code=400)
        return attrs


class AdminContactCheckSerializer(serializers.Serializer):
    guests = serializers.JSONField(required=True)

    def to_representation(self, instance):
        response = super(AdminContactCheckSerializer, self).to_representation(instance)
        for guest in response.get('guests'):
            try:
                validate_email(response['guests'][guest])
                response['guests'][guest] = "is_valid"
            except ValErr:
                try:
                    try:
                        phone_number = phonenumbers.parse(response['guests'][guest])
                    except:
                        try:
                            if response['guests'][guest][0] == '8':
                                response['guests'][guest] = response['guests'][guest].replace('8', '+7', 1)
                            else:
                                response['guests'][guest] = '+' + response['guests'][guest]
                        except IndexError:
                            response['guests'][guest] = "not_valid"
                        phone_number = phonenumbers.parse(response['guests'][guest])
                    if phonenumbers.is_valid_number(phone_number):
                        response['guests'][guest] = "is_valid"
                    else:
                        response['guests'][guest] = "not_valid"
                except AttributeError:
                    response['guests'][guest] = "not_valid"
                except phonenumbers.phonenumberutil.NumberParseException:
                    response['guests'][guest] = "not_valid"
        return response
