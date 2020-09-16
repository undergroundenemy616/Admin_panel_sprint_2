from rest_framework import serializers
from licenses.models import License
from offices.models import Office


class LicenseSerializer(serializers.ModelSerializer):
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), many=False, required=False)

    class Meta:
        model = License
        fields = '__all__'
        depth = 1
