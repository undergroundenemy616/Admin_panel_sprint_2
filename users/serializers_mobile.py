import ipinfo
from django.db.models import Q
from rest_framework import serializers

from bookings.models import Booking
from files.models import File
from files.serializers_mobile import MobileBaseFileSerializer
from users.models import Account, AppEntrances, User
from users.serializers import AccountSerializer


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


class MobileAccountMeetingSearchSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', required=False)
    email = serializers.CharField(source='user.email', required=False)

    class Meta:
        model = Account
        fields = ['id', 'first_name', 'last_name',
                  'middle_name', 'phone_number', 'email', 'gender']

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
