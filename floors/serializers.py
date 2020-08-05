from rest_framework import serializers
from floors.models import Floor


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'
        depth = 1
