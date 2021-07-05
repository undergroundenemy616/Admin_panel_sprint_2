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
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from booking_api_django_new.settings import DEBUG, KEY_EXPIRATION_EMAIL, KEY_EXPIRATION
from core.handlers import ResponseException
from bookings.models import Booking
from files.models import File
from users.models import Account, AppEntrances, User
from users.serializers import AccountSerializer
from users.tasks import send_email, send_sms


def send_conformation_code(recipient: str, subject="", ttl=60, key=None, phone=False) -> None:
    conformation_code = "".join([random.choice("0123456789") for _ in range(4)])
    if not key:
        key = recipient
    if KEY_EXPIRATION_EMAIL - cache.ttl(key) < KEY_EXPIRATION:
        detail = {"detail": 'Message already sent!',
                  "time": KEY_EXPIRATION-(KEY_EXPIRATION_EMAIL - cache.ttl(key))}
        raise ValidationError(detail=detail, code=400)
    cache.set(key, conformation_code, ttl)
    if not phone:
        send_email.delay(email=recipient, subject=subject,
                         message="Код подтверждения: " + conformation_code)
    else:
        send_sms.delay(phone_number=recipient, message="Код подтверждения: " + conformation_code)


def confirm_code(key, code) -> bool:
    if cache.get(key) == code:
        return True
    return False


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
    phone_number = serializers.CharField(source='user.phone_number')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = Account
        fields = ['id', 'email', 'gender', 'last_name', 'first_name', 'phone_number', 'user', 'birth_date']


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
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    middle_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
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
            response["activated"] = user.is_active
            del self.context['request'].session['confirm']
            return response

        if self.validated_data.get('code'):
            if cache.get(self.validated_data.get('email')) == self.validated_data.get('code'):
                self.context['request'].session['confirm'] = True
                cache.delete(self.validated_data.get('email'))
                return {'message': 'email confirm'}
            else:
                raise ResponseException("Wrong or expired code")

        send_conformation_code(recipient=self.validated_data.get('email'), subject="Подтверждение почты",
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
            user = user[0]
            if not user.password:
                raise ResponseException("Incorrect email or password", status_code=400)
            is_correct = user.check_password(attrs.get('password'))
            if not self.context['request'].session.get('login_count'):
                self.context['request'].session['login_count'] = 0
            if self.context['request'].session.get('login_count') >= 5:
                raise ValidationError(detail={"detail": "Too many attempts",
                                              "time": self.context['request'].session._get_session_from_db().expire_date})
            if not is_correct:
                self.context['request'].session['login_count'] += 1
                raise ResponseException('Incorrect email or password', status_code=400)
            user_logged_in.send(sender=user.__class__, user=user)
            token_serializer = TokenObtainPairSerializer()
            token = token_serializer.get_token(user=user)
            attrs = dict()
            attrs["refresh_token"] = str(token)
            attrs["access_token"] = str(token.access_token)
            attrs["activated"] = user.is_active
            return attrs
        attrs['user_has_password'] = bool(user[0].password)
        return attrs


class MobilePasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=64)
    new_password = serializers.CharField(max_length=64)

    def validate(self, attrs):
        if not self.context['request'].session.get('pass_change_count'):
            self.context['request'].session['pass_change_count'] = 0
        if self.context['request'].session.get('pass_change_count') >= 5:
            raise ValidationError(detail={"detail": "Too many attempts",
                                          "time": self.context['request'].session._get_session_from_db().expire_date})
        if not self.context['request'].user.check_password(attrs['old_password']):
            self.context['request'].session['pass_change_count'] += 1
            raise ValidationError(detail="wrong password", code=400)
        if not DEBUG:
            validate_password(attrs['new_password'], user=self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()

    def to_representation(self, instance):
        response = dict()
        token_serializer = TokenObtainPairSerializer()
        token = token_serializer.get_token(user=self.context['request'].user)
        response['message'] = "OK"
        response['access_token'] = str(token.access_token)
        response['refresh_token'] = str(token)
        response['activated'] = self.context['request'].user.is_active
        return response


class MobilePasswordResetSetializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(required=False)
    new_password = serializers.CharField(max_length=512, required=False)

    def validate(self, attrs):
        if not User.objects.filter(email=attrs.get('email')).exists():
            raise ResponseException("Wrong email")
        if self.context['request'].session.get('confirm'):
            attrs['user'] = User.objects.get(email=attrs.get('email'))
            if not DEBUG and attrs.get('new_password'):
                validate_password(attrs['new_password'], user=attrs['user'])
        return attrs

    @atomic()
    def reset(self):

        if self.validated_data.get('code'):
            if cache.get(self.validated_data.get('email')) == self.validated_data.get('code'):
                self.context['request'].session['confirm'] = True
                cache.delete(self.validated_data.get('email'))
                return {'message': 'email confirm'}
            else:
                raise ResponseException("Wrong or expired code")

        if self.context['request'].session.get('confirm') and self.validated_data.get('new_password'):
            self.validated_data['user'].set_password(self.validated_data.get('new_password'))
            self.validated_data['user'].save()
            response = dict()
            user_logged_in.send(sender=self.validated_data['user'].__class__, user=self.validated_data['user'])
            token_serializer = TokenObtainPairSerializer()
            token = token_serializer.get_token(user=self.validated_data['user'])
            response["refresh_token"] = str(token)
            response["access_token"] = str(token.access_token)
            response["activated"] = self.validated_data['user'].is_active
            del self.context['request'].session['confirm']
            cache.delete(self.validated_data.get('email'))
            return response

        send_conformation_code(recipient=self.validated_data.get('email'), subject="Подтверждение почты для сброса пароля",
                               ttl=KEY_EXPIRATION_EMAIL)

        return {'message': 'email with conformation code sent'}


class MobileConformationSerializer(serializers.Serializer):
    user_identification = serializers.CharField(allow_blank=False)
    code = serializers.CharField(max_length=4, required=False)
    email = serializers.BooleanField(required=False)

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
        attrs['email'] = email
        if email:
            if User.objects.filter(email=attrs['user_identification']).exists():
                raise ResponseException("User with this email already exists")
        else:
            try:
                attrs['user_identification'] = User.normalize_phone(attrs.get('user_identification'))
            except ValueError as e:
                raise ResponseException(e)
            if User.objects.filter(phone_number=attrs['user_identification']).exists():
                raise ResponseException("User with this phone already exists")
        return attrs

    def send_code(self):
        key = self.validated_data.get('user_identification') + '_' + str(self.context['request'].user.id)
        sent_to = 'почты.' if self.validated_data.get('email') else 'телефона.'
        send_conformation_code(recipient=self.validated_data.get('user_identification'),
                               subject="Подтверждение "+sent_to, ttl=KEY_EXPIRATION_EMAIL,
                               key=key, phone=not self.validated_data.get('email'))
        return {"detail": "Conformation code was sent"}

    def confirm(self):
        if confirm_code(key=self.validated_data['user_identification'] + '_' + str(self.context['request'].user.id),
                        code=self.validated_data.get('code')):
            key = 'email' if self.validated_data.get('email') else 'phone'
            self.context['request'].session[f'{key}_confirm'] = self.validated_data['user_identification']
            return {"detail": "Confirmed"}
        else:
            raise ResponseException("Wrong or expired code")


class MobileAccountMeetingSearchSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', required=False)
    email = serializers.CharField(source='user.email', required=False)

    class Meta:
        model = Account
        fields = ['id', 'first_name', 'last_name',
                  'middle_name', 'phone_number', 'email', 'gender']

    def to_representation(self, instance):
        response = super(MobileAccountMeetingSearchSerializer, self).to_representation(instance)

        if Booking.objects.is_user_overflowed(account=instance,
                                              date_from=self.context['request'].query_params.get('date_from'),
                                              date_to=self.context['request'].query_params.get('date_to'),
                                              room_type=True):
            response['is_available'] = False
        else:
            response['is_available'] = True

        return response


class MobileSelfUpdateSerializer(serializers.ModelSerializer):
    phone_code = serializers.IntegerField(required=False)
    gender = serializers.CharField(required=False, source='account.gender')
    last_name = serializers.CharField(required=False, source='account.last_name')
    first_name = serializers.CharField(required=False, source='account.first_name')
    middle_name = serializers.CharField(required=False, source='account.middle_name')

    class Meta:
        model = User
        fields = ['email', 'password', 'gender', 'last_name', 'first_name', 'phone_number', 'phone_code', 'middle_name']

    def validate(self, attrs):
        if attrs.get('email') and self.instance.email != attrs['email'] and User.objects.filter(
                email=attrs['email']):
            raise ResponseException("User with this email already exists")

        if self.instance and self.instance.password and attrs.get('password'):
            raise ResponseException("User already have password")

        if not DEBUG and attrs.get('password'):
            validate_password(attrs['password'], user=self.context['request'].user)

        if self.instance and attrs.get('email') and self.instance.email != attrs.get('email') and \
                not self.context['request'].session.get('email_confirm') == attrs.get('email'):
            raise ResponseException("Need email conformation for change email")

        if self.instance and attrs.get('phone_number') and self.instance.phone_number != attrs.get('phone_number') and \
                not self.context['request'].session.get('phone_confirm') == attrs.get('phone_number'):
            raise ResponseException("Need phone conformation code for change phone")

        return attrs

    @atomic()
    def update(self, instance, validated_data):
        account_params = validated_data.pop('account') if validated_data.get('account') else None
        if account_params:
            for param in account_params:
                setattr(instance.account, param, account_params[param])
                instance.account.save()
        instance = super(MobileSelfUpdateSerializer, self).update(instance=instance, validated_data=validated_data)
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
            instance.save()
        if self.context['request'].session.get('email_confirm'):
            del self.context['request'].session['email_confirm']
        if self.context['request'].session.get('phone_confirm'):
            del self.context['request'].session['phone_confirm']
        return instance

    def to_representation(self, instance):
        return MobileAccountSerializer(instance=instance.account).data

