from rest_framework import serializers

from groups.models import Group
from users.models import User, Account


class PanelRegisterUserSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def save(self, **kwargs):
        user, created = User.objects.get_or_create(phone_number=self.data['phone_number'])
        account, account_created = Account.objects.get_or_create(user=user)
        user_group = Group.objects.get(access=4, is_deletable=False, title='Посетитель')
        if not user_group:
            user_group = Group.objects.get(access=4, is_deletable=False, title='Guests')
        if account_created:
            user.is_active = True
            user.save(update_fields=['is_active'])
            account.groups.add(user_group)
        elif not user.is_active and user_group not in account.groups.all():
            user.is_active = True
            user.save(update_fields=['is_active'])
            account.groups.add(user_group)
        elif not user.is_active and user_group in account.groups.all():
            user.is_active = True
            user.save(update_fields=['is_active'])
        return account
