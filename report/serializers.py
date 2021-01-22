from rest_framework import serializers
from report.models import Report
from files.models import File
from files.serializers import FileSerializer
from rest_framework.mixins import status


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
        response['office'] = {"id": instance.id, "title": instance.title}
        response['images'] = [FileSerializer(instance=image).data for image in instance.images.all()]
        return response

    def validate(self, attrs):
        office = attrs['office']
        if not office:
            raise serializers.ValidationError("Office is not found", status.HTTP_404_NOT_FOUND)
        if not office.service_email:
            raise serializers.ValidationError("Office email is not found", status.HTTP_400_BAD_REQUEST)
        if not office.title:
            raise serializers.ValidationError("Office title is not found", status.HTTP_400_BAD_REQUEST)
        return attrs
