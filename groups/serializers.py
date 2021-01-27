from rest_framework import serializers

from groups.models import Group
from users.models import Account, User
from users.serializers import AccountSerializer


class SwaggerGroupsParametrs(serializers.Serializer):
    id = serializers.UUIDField(required=False)


class SwaggerImportSingleGroupParametrs(serializers.Serializer):
    file = serializers.FileField(required=True)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

    def to_representation(self, instance):
        response = super(GroupSerializer, self).to_representation(instance)
        pre_defined = instance.is_deletable
        response['pre_defined'] = not pre_defined
        legacy_access = Group.to_legacy_access(access=instance.access)
        if not legacy_access:
            raise serializers.ValidationError('Invalid group access')
        response.update(legacy_access)
        users_in_group = User.objects.filter(account__groups=response['id'])
        response['count'] = len(users_in_group)
        response['users'] = [AccountSerializer(instance=user.account).data for user in users_in_group]
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


class UpdateGroupSerializer(GroupSerializer):
    title = serializers.CharField(required=False)
    global_can_write = serializers.BooleanField(required=False, write_only=True)
    global_can_manage = serializers.BooleanField(required=False, write_only=True)

    def update(self, instance, validated_data):
        instance: Group
        legacy_rights = Group.to_legacy_access(instance.access)
        validated_data['access'] = Group.from_legacy_access(
            w=validated_data.pop('global_can_write', None) or legacy_rights['global_write'],
            m=validated_data.pop('global_can_manage', None) or legacy_rights['global_manage'],
            s=False
        )
        return super(UpdateGroupSerializer, self).update(instance, validated_data)


class UpdateGroupUsersSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), required=True)
    users = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), many=True, required=True, allow_empty=True)


def base_group_serializer(group: Group):
    return {
        'id': str(group.id),
        'title': group.title
    }
