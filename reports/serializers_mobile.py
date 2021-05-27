from rest_framework import serializers

from files.serializers_mobile import MobileBaseFileSerializer
from reports.models import Report


class MobileReportSerializer(serializers.ModelSerializer):
    images = MobileBaseFileSerializer(required=False, many=True, allow_null=True)

    class Meta:
        fields = '__all__'
        model = Report

    def to_representation(self, instance):
        response = super(MobileReportSerializer, self).to_representation(instance)
        response['office'] = {
            "id": instance.office.id,
            "title": instance.title}
        return response
