from rest_framework import serializers
from tables.models import Table


class TableSerializer(serializers.ModelSerializer):
	current_rating = serializers.ReadOnlyField()

	class Meta:
		model = Table
		fields = '__all__'