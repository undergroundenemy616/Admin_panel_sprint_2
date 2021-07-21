from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from clients.models import Client, Domain


class ClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)

    class Meta:
        model = Client
        fields = ['id', 'name', 'paid_until', 'created_on']
        read_only_fields = ['created_on', 'auto_create_schema', 'auto_drop_schema',
                            'domain_url', 'domain_subfolder', 'schema_name']

    def validate_name(self, value):
        if value in Domain.objects.values_list('domain', flat=True):
            raise ValidationError(f"Domain {value} already exists")
        return value

    def create(self, validated_data):
        tenant = Client.objects.create(name=validated_data['name'], schema_name=validated_data['name'])
        domain = f"{validated_data['name']}.{self.context['request'].META['HTTP_HOST']}"
        Domain.objects.create(domain=domain, tenant=tenant, is_primary=True)
        return tenant

    def update(self, instance, validated_data):
        instance.paid_until = validated_data['paid_until']
        instance.save()
        return instance


