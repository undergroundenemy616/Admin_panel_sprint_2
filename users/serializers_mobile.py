import random

from django.contrib.auth.password_validation import validate_password
import ipinfo
from django.contrib.auth import user_logged_in
from django.core.validators import validate_email
from django.core.cache import cache
from django.db.transaction import atomic
from django.db.models import Q
from rest_framework import serializers
from django.core.exceptions import ValidationError as ValErr
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from booking_api_django_new.settings import DEBUG, KEY_EXPIRATION_EMAIL
from core.handlers import ResponseException
from bookings.models import Booking
from files.models import File
from files.serializers_mobile import MobileBaseFileSerializer
from users.models import Account, AppEntrances, User
from users.serializers import AccountSerializer
from users.tasks import send_email, send_sms


def sent_conformation_code(recipient: str, subject="", ttl=60, key=None, phone=False) -> None:
    conformation_code = "".join([random.choice("0123456789") for _ in range(4)])
    if not key:
        key = recipient
    cache.set(key, conformation_code, ttl)
    if not phone:
        send_email.delay(email=recipient, subject=subject,
                         message="Код подтверждения: " + conformation_code)
    else:
        send_sms.delay(phone_number=recipient, message="Код подтверждения: " + conformation_code)



class MobileEntranceCollectorSerializer(serializers.ModelSerializer):
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


class MobileLoginOrRegisterSerializer(serializers.Serializer):
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


class MobileAccountSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name', allow_blank=True, allow_null=True)
    lastname = serializers.CharField(source='last_name', allow_blank=True, allow_null=True)
    middlename = serializers.CharField(source='middle_name', allow_blank=True, allow_null=True)
    birthday = serializers.DateField(source='birth_date', allow_null=True)
    photo = MobileBaseFileSerializer(required=False, allow_null=True)

    class Meta:
        model = Account
        exclude = ['first_name', 'last_name', 'middle_name', 'birth_date']

    def to_representation(self, instance):
        response = super(MobileAccountSerializer, self).to_representation(instance)
        response['phone_number'] = instance.user.phone_number if instance.user.phone_number else instance.phone_number
        response['email'] = instance.user.email if instance.user.email else instance.email
        response['has_cp_access'] = True if instance.user.email else False
        return response


class MobileAccountUpdateSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name', required=False, allow_blank=True, allow_null=True)
    lastname = serializers.CharField(source='last_name', required=False, allow_blank=True, allow_null=True)
    middlename = serializers.CharField(source='middle_name', required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
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

    def validate(self, attrs):
        if attrs.get('email') == "":
            attrs['email'] = None
        return attrs


class MobileUserRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    code = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    middle_name = serializers.CharField(required=False)
    gender = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)

    def validate(self, attrs):
        if User.objects.filter(email=attrs['email']).exists():
            raise ResponseException("User with this email already exists")
        if attrs.get('password'):
            if not DEBUG:
                validate_password(attrs.get('password'))
        if attrs.get('phone_number'):
            try:
                attrs['phone_number'] = User.normalize_phone(attrs['phone_number'])
            except ValueError as e:
                raise ResponseException(e)
        return attrs


    @atomic()
    def register(self):
        if self.context['request'].session.get('confirm') and self.validated_data.get('password'):
            # if not self.validated_data.get('password'):
            #     raise ResponseException("Password is required field", status_code=400)
            user = User.objects.create(email=self.validated_data.pop('email'))
            user.set_password(self.validated_data.pop('password'))
            user.save()
            if self.validated_data.get('code'):
                self.validated_data.pop('code')
            Account.objects.create(user=user, **self.validated_data)
            response = dict()
            token_serializer = TokenObtainPairSerializer()
            token = token_serializer.get_token(user=user)
            user_logged_in.send(sender=user.__class__, user=user)
            response["refresh_token"] = str(token)
            response["access_token"] = str(token.access_token)
            del self.context['request'].session['confirm']
            return response

        if self.validated_data.get('code'):
            if cache.get(self.validated_data.get('email')) == self.validated_data.get('code'):
                self.context['request'].session['confirm'] = True
                cache.delete(self.validated_data.get('email'))
                return {'message': 'email confirm'}
            else:
                raise ResponseException("Wrong or expired code")

        sent_conformation_code(recipient=self.validated_data.get('email'), subject="Подтверждение почты",
                               ttl=KEY_EXPIRATION_EMAIL)

        return {'message': 'email with conformation code sent'}


class MobileUserLoginSerializer(serializers.Serializer):
    user_identification = serializers.CharField(write_only=True)
    password = serializers.CharField(required=False)
    user_has_password = serializers.BooleanField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    access_token = serializers.CharField(read_only=True)
    activated = serializers.BooleanField(read_only=True)

    def validate(self, attrs):
        email = False
        try:
            validate_email(attrs.get('user_identification'))
            email = True
        except ValErr:
            try:
                attrs['user_identification'] = User.normalize_phone(attrs.get('user_identification'))
            except ValueError:
                raise ResponseException("Wrong format of email or phone", status_code=400)
        if email:
            user = User.objects.filter(email=attrs.get('user_identification'))
        else:
            user = User.objects.filter(phone_number=attrs.get('user_identification'))

        if not user:
            raise ResponseException("User doesn't exists")

        if attrs.get('password'):
            response = dict()
            if not user:
                raise ResponseException("Incorrect email or password", status_code=400)
            user = user[0]
            if not user.password:
                raise ResponseException("Incorrect email or password", status_code=400)
            is_correct = user.check_password(attrs.get('password'))
            if not is_correct:
                raise ResponseException('Incorrect email or password', status_code=400)
            user_logged_in.send(sender=user.__class__, user=user)
            token_serializer = TokenObtainPairSerializer()
            token = token_serializer.get_token(user=user)
            response["refresh_token"] = str(token)
            response["access_token"] = str(token.access_token)
            response["activated"] = user.is_active
            return response
        attrs['user_has_password'] = bool(user[0].password)
        return attrs


class MobilePasswordChangeSerializer(serializers.Serializer):
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


class MobilePasswordResetSetializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(required=False)

    def validate(self, attrs):
        if not User.objects.filter(email=attrs.get('email')).exists():
            raise ResponseException("Wrong email")
        return attrs

    @atomic()
    def reset(self):
        if self.validated_data.get('code'):
            if cache.get(self.validated_data.get('email')) == self.validated_data.get('code'):
                password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])
                send_email.delay(email=self.validated_data.get('email'), subject="Сброс пароля",
                                 message="Новый пароль: " + password)
                user = get_object_or_404(User, email=self.validated_data.get('email'))
                user.set_password(password)
                user.save()
                cache.delete(self.validated_data.get('email'))
                return {'message': 'password reset'}
            else:
                raise ResponseException("Wrong or expired code")

        sent_conformation_code(recipient=self.validated_data.get('email'), subject="Подтверждение почты для сброса пароля",
                               ttl=KEY_EXPIRATION_EMAIL)

        return {'message': 'email with conformation code sent'}


class MobileEmailConformationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def sent_code(self):
        key = self.validated_data.get('email') + '_' + self.context['id']
        sent_conformation_code(recipient=self.validated_data.get('email'),
                               subject="Подтверждене почты", ttl=KEY_EXPIRATION_EMAIL,
                               key=key)


class MobilePhoneConformationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate(self, attrs):
        try:
            attrs['phone_number'] = User.normalize_phone(attrs.get('phone_number'))
        except ValueError as e:
            raise ResponseException(e)
        return attrs

    def sent_code(self):
        key = self.validated_data.get('phone_number') + '_' + self.context['id']
        sent_conformation_code(recipient=self.validated_data.get('phone_number'),
                               ttl=KEY_EXPIRATION_EMAIL, key=key, phone=True)

class MobileAccountMeetingSearchSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', required=False)

    class Meta:
        model = Account
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'phone_number']

    def to_representation(self, instance):
        response = super(MobileAccountMeetingSearchSerializer, self).to_representation(instance)
        account_bookings = Booking.objects.filter(Q(user_id=response['id'])
                                                  &
                                                  Q(status__in=['waiting', 'active'])
                                                  &
                                                  (Q(date_from__lt=self.context['request'].query_params.get('date_to'),
                                                     date_to__gte=self.context['request'].query_params.get('date_to'))
                                                   |
                                                   Q(date_from__lte=self.context['request'].query_params.get('date_from'),
                                                     date_to__gt=self.context['request'].query_params.get('date_from'))
                                                   |
                                                   Q(date_from__gte=self.context['request'].query_params.get('date_from'),
                                                     date_to__lte=self.context['request'].query_params.get('date_to')))
                                                  &
                                                  Q(date_from__lt=self.context['request'].query_params.get('date_to')))

        if account_bookings:
            response['occupied_time'] = []
            for booking in account_bookings:
                response['occupied_time'].append({
                    'date_from': booking.date_from,
                    'date_to': booking.date_to
                })
            response['is_available'] = False
        else:
            response['occupied_time'] = []
            response['is_available'] = True

        return response
