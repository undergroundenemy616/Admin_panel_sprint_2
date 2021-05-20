from rest_framework import serializers

from files.models import File


class MobileBaseFileSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    path = serializers.CharField()
    thumb = serializers.CharField()


class MobileFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    title = serializers.CharField(required=False)

    class Meta:
        model = File
        fields = ['file', 'title']
