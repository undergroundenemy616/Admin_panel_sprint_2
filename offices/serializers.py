from rest_framework import serializers
from floors.models import Floor
from offices.models import Office
from files.models import File
from licenses.models import License
from floors.serializers import FloorSerializer


# class EditOfficeSerializer(serializers.ModelSerializer):
#     license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(), required=False)
#     images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
#     floors_number = serializers.IntegerField(min_value=0, required=False)
#
#     class Meta:
#         model = Office
#         fields = '__all__'


class OfficeSerializer(serializers.ModelSerializer):
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(), required=False, write_only=True)
    images = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False, write_only=True)
    floors = FloorSerializer(many=True, read_only=True)
    floors_number = serializers.IntegerField(min_value=0, max_value=84, required=False)  # floors count

    class Meta:
        model = Office
        fields = '__all__'
        read_only_fields = ('occupied',
                            'capacity',
                            'occupied_tables',
                            'capacity_tables',
                            'occupied_meeting',
                            'capacity_meeting',
                            # 'floors_number',
                            'floors')

    def create(self, validated_data):
        validated_data.pop('license', None)
        floors_number = validated_data.pop('floors_number', 0)
        instance = super(OfficeSerializer, self).create(validated_data)
        floors_to_save = [Floor(title=str(n + 1), office=instance) for n in range(0, floors_number)]
        Floor.objects.bulk_create(floors_to_save)
        return instance

    def update(self, instance, validated_data):
        floors_number = validated_data.pop('floors_number', None)
        license_id = validated_data.pop('license', None)
        if license_id:
            entity = License.objects.get(pk=license_id)
            entity.office = instance
            entity.save()
            # Todo test it
        if floors_number is not None and floors_number > instance.floors_number:
            floors_to_save = [Floor(title=str(n + 1), office=instance) for n in range(instance.floors_number,
                                                                                      floors_number)]
            Floor.objects.bulk_create(floors_to_save)
        return super(OfficeSerializer, self).update(instance, validated_data)
