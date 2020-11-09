from rest_framework import serializers
from groups.models import Group
from users.models import User
from users.serializers import UserSerializer


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

    def to_representation(self, instance):
        response = super(GroupSerializer, self).to_representation(instance)
        pre_defined = response.pop('is_deletable')
        response['pre_defined'] = not pre_defined
        legacy_access = Group.to_legacy_access(access=response.pop('access'))
        if not legacy_access:
            raise serializers.ValidationError('Invalid group access')
        response.update(legacy_access)
        users_in_group = User.objects.filter(account__groups=response['id'])
        response['count'] = len(users_in_group)
        response['users'] = [UserSerializer(user).data for user in users_in_group]
        return response


class CreateGroupSerializer(GroupSerializer):
    global_can_write = serializers.BooleanField(required=True, write_only=True)
    global_can_manage = serializers.BooleanField(required=True, write_only=True)

    def create(self, validated_data):
        validated_data['access'] = Group.from_legacy_access(
            w=validated_data.pop('global_can_write'),
            m=validated_data.pop('global_can_manage'),
            s=False
        )
        validated_data['is_deletable'] = True
        return Group.objects.create(**validated_data)
