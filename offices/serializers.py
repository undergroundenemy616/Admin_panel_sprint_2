from rest_framework import serializers
from offices.models import Office


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'
        # depth = 1
