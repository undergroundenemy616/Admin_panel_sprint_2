from rest_framework import serializers
from groups.models import Group
from users.models import User


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

    def to_representation(self, instance):
        response = super(GroupSerializer, self).to_representation(instance)
        pre_defined = response.pop('is_deletable')
        response['pre_defined'] = not pre_defined
        access = response.pop('access')
        if access == 1:
            response['global_manage'] = True
            response['global_read'] = True
            response['global_service'] = True
            response['global_write'] = True
        elif access == 2:
            response['global_manage'] = True
            response['global_read'] = True
            response['global_service'] = False
            response['global_write'] = True
        elif access == 3:
            response['global_manage'] = False
            response['global_read'] = True
            response['global_service'] = False
            response['global_write'] = True
        elif access == 4:
            response['global_manage'] = False
            response['global_read'] = True
            response['global_service'] = False
            response['global_write'] = False
        users_in_group = User.objects.filter(account__groups=response['id'])
        response['count'] = len(users_in_group)
        response['users'] = [user.account.id for user in users_in_group]
        return response
