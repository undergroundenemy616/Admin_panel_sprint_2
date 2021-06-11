from rest_framework import serializers

from files.models import File
from reports.models import Report


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

