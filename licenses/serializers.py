from rest_framework import serializers
from licenses.models import License
from offices.models import Office


class SwaggerLicenseParametrs(serializers.Serializer):
    free = serializers.CharField(required=False, max_length=5)


class LicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = License
        fields = '__all__'
        depth = 1
