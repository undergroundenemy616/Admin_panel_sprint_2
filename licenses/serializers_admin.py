from rest_framework import serializers

from licenses.models import License


class AdminLicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = License
        fields = '__all__'
        depth = 1
