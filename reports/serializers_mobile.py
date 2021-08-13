from django.core.exceptions import ValidationError as ValEr
from django.core.validators import validate_email
from rest_framework import serializers

from booking_api_django_new.settings import EMAIL_FOR_DEMOS
from core.handlers import ResponseException
from files.models import File
from reports.models import Report
from users.models import User
from users.tasks import send_email


class MobileReportSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)

    class Meta:
        fields = '__all__'
        model = Report

    def to_representation(self, instance):
        response = super(MobileReportSerializer, self).to_representation(instance)
        response['office'] = {
            "id": instance.office.id,
            "title": instance.office.title}
        return response


class MobileRequestDemoSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone_number = serializers.CharField()
    company = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        try:
            attrs['phone_number'] = User.normalize_phone(attrs['phone_number'])
        except ValueError as e:
            raise ResponseException(e)
        if attrs.get('email'):
            try:
                validate_email(attrs['email'])
            except ValEr:
                raise ResponseException(ValEr)
        return attrs

    def send_email(self):
        if self.context['request'].session.get('count_emails') \
                and self.context['request'].session['count_emails'] < 5:
            self.context['request'].session['count_emails'] += 1
        elif self.context['request'].session.get('count_emails') \
                and self.context['request'].session['count_emails'] >= 5:
            raise ResponseException("Too many emails sent")
        else:
            self.context['request'].session['count_emails'] = 1
        message = f"Имя: {self.validated_data['name']} \nТелефон: {self.validated_data['phone_number']}"
        if self.validated_data.get('email'):
            message = message + f"\nПочта: {self.validated_data['email']}"
        if self.validated_data.get('company'):
            message = message + f"\nКомпания: {self.validated_data['company']}"
        send_email.delay(email=EMAIL_FOR_DEMOS, subject='Запрос на демо версию из приложения', message=message)
