from rest_framework import serializers

from files.models import File
from offices.models import Office
from room_types.models import RoomType
from rooms.models import Room


class RoomTypeSerializer(serializers.ModelSerializer):
    """
    Serialize object from table RoomType
    """
    class Meta:
        model = RoomType
        fields = '__all__'


class CreateUpdateRoomTypeSerializer(serializers.ModelSerializer):
    title = serializers.ListField(max_length=50, required=True)
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), required=True)
    icon = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), required=False)
    color = serializers.CharField(min_length=6, max_length=8, default='#0079c1')
    bookable = serializers.BooleanField(default=False, required=False)
    work_interval_days = serializers.IntegerField(default=0, required=False)
    work_interval_hours = serializers.IntegerField(default=0, required=False)
    unified = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = RoomType
        exclude = ['is_deletable']

    def to_representation(self, instance):
        if isinstance(instance, list):
            response = []
            for room_type in instance:
                response.append(RoomTypeSerializer(room_type).data)
            return response
        response = RoomTypeSerializer(instance).data
        return response

    def create(self, validated_data):
        titles = validated_data.pop('title')
        office = validated_data.pop('office')
        if len(titles) > 1:
            types_to_create = []
            for title in titles:
                type_exist = RoomType.objects.filter(title=title, office=office)
                if type_exist:
                    continue
                types_to_create.append(RoomType(title=title, office=office))
            RoomType.objects.bulk_create(types_to_create)
            return types_to_create
        type_exist = RoomType.objects.filter(title=titles[0], office=office)
        if type_exist:
            raise serializers.ValidationError('Type already exist')
        return RoomType.objects.create(title=titles[0], office=office, icon=validated_data['icon'],
                                       color=validated_data['color'], bookable=validated_data['bookable'],
                                       work_interval_days=validated_data['work_interval_days'],
                                       work_interval_hours=validated_data['work_interval_hours'],
                                       unified=validated_data['unified'])

    def update(self, instance, validated_data):
        title = validated_data.pop('title')
        validated_data['title'] = title[0]
        return super(CreateUpdateRoomTypeSerializer, self).update(instance, validated_data)


class DestroyRoomTypeSerializer(serializers.ModelSerializer):
    type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.filter(is_deletable=True))

    class Meta:
        model = RoomType
        fields = ['type']

    def update(self, instance, validated_data):
        rooms_with_type = Room.objects.filter(type=instance.id)
        default_room_type = RoomType.objects.filter(office=instance.office.id, title='Рабочее место').first()
        for room in rooms_with_type:
            room.objects.update(type=default_room_type)
        return instance


