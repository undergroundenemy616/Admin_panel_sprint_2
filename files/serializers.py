from rest_framework import serializers
from files.models import File



class FileSerializer(serializers.ModelSerializer):
    file = serializers.ImageField()

    class Meta:
        model = File
        fields = ['file']
        depth = 1

    def create(self, validated_data):
        pass
