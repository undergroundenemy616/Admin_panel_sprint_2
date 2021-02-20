from rest_framework import serializers

from files.models import File
from files.serializers import FileSerializer
from reports.models import Report


class SwaggerReportParametrs(serializers.Serializer):
    id = serializers.UUIDField()


class ReportSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(),
                                                required=False,
                                                many=True)

    class Meta:
        fields = '__all__'
        model = Report

    def to_representation(self, instance):
        response = super(ReportSerializer, self).to_representation(instance)
        response['office'] = {"id": instance.office.id, "title": instance.title}
        response['images'] = [{
            "title": image.title,
            "path": image.path,
            "thumb": image.thumb,
            "size": image.size,
            "width": image.width,
            "height": image.height
        } for image in instance.images.all()]
        return response
