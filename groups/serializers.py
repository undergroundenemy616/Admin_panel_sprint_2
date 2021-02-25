from core.handlers import ResponseException
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from rest_framework import serializers, status


from booking_api_django_new.validate_phone_number import validate_phone_number
from groups.models import Group
from users.models import Account, User
from users.serializers import AccountSerializer, AccountSerializerLite


def validate_csv_file_extension(file):
    if '.csv' not in str(file):
        raise ValidationError('Unsupported file extension')


class SwaggerGroupsParametrs(serializers.Serializer):
    id = serializers.UUIDField(required=False)


class GroupSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False)

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
        # users_in_group = User.objects.filter(account__groups=response['id'])
        response['count'] = len(instance.accounts.all())
        response['users'] = [AccountSerializerLite(instance=account).data for account in instance.accounts.all()]
        return response


class GroupSerializerLite(serializers.ModelSerializer):
    file = serializers.FileField(required=False)

    class Meta:
        model = Group
        fields = '__all__'

    def to_representation(self, instance):
        response = super(GroupSerializerLite, self).to_representation(instance)
        is_deletable = instance.is_deletable
        response['pre_defined'] = not is_deletable
        legacy_access = Group.to_legacy_access(access=instance.access)
        if not legacy_access:
            raise serializers.ValidationError('Invalid group access')
        response.update(legacy_access)
        users_in_group = User.objects.filter(account__groups=response['id'])
        response['count'] = len(users_in_group)
        # response['users'] = [user.account.id for user in users_in_group]
        for key in ['is_deletable', 'access']:
            response.pop(key)
        return response


class GroupSerializerCSV(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = Group
        fields = ('file', )

    def create(self, validated_data):
        validate_csv_file_extension(file=validated_data['file'])

        groups_before = Group.objects.all().count()

        file = validated_data.pop('file')

        list_of_group_titles = []

        for chunk in list(file.read().splitlines()):
            try:
                try:
                    list_of_group_titles.append(chunk.decode('utf8').split(',')[1])
                except IndexError:
                    list_of_group_titles.append(chunk.decode('utf8'))
            except UnicodeDecodeError:
                try:
                    list_of_group_titles.append(chunk.decode('cp1251').split(',')[1])
                except IndexError:
                    list_of_group_titles.append(chunk.decode('cp1251'))

        groups_to_create = []

        for group in list_of_group_titles:
            groups_to_create.append(Group(title=group, description=None, access=4, is_deletable=True))
        Group.objects.bulk_create(groups_to_create, ignore_conflicts=True)

        groups_after = Group.objects.all()

        groups_processed = len(list_of_group_titles)

        groups_created = groups_after.count() - groups_before

        return ({
            "message": "OK",
            "counters": {
                "groups_processed": groups_processed,
                "groups_created": groups_created,
            },
            "result": GroupSerializer(instance=groups_after, many=True).data
        })


class GroupSerializerWithAccountsCSV(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = Group
        fields = ('file', )

    def create(self, validated_data):
        validate_csv_file_extension(file=validated_data['file'])

        file = validated_data.pop('file')

        list_of_group_titles = []
        list_of_phone_numbers = []
        groups_users_relation = []

        for chunk in list(file.read().splitlines()):
            try:
                if validate_phone_number(chunk.decode('utf8').split(',')[0]):
                    list_of_phone_numbers.append(chunk.decode('utf8').split(',')[0])
                list_of_group_titles.append(chunk.decode('utf8').split(',')[1])
                groups_users_relation.append({'phone_number': chunk.decode('utf8').split(',')[0],
                                              'group': chunk.decode('utf8').split(',')[1]})
            except UnicodeDecodeError:
                if validate_phone_number(chunk.decode('cp1251').split(',')[0]):
                    list_of_phone_numbers.append(chunk.decode('cp1251').split(',')[0])
                list_of_group_titles.append(chunk.decode('cp1251').split(',')[1])
                groups_users_relation.append({'phone_number': chunk.decode('cp1251').split(',')[0],
                                              'group': chunk.decode('cp1251').split(',')[1]})

        groups_to_create = []
        users_to_create = []
        accounts_to_create = []

        for group in list_of_group_titles:
            groups_to_create.append(Group(title=group, description=None, access=4, is_deletable=True))
        group = Group.objects.bulk_create(groups_to_create, ignore_conflicts=True)

        groups_created = len(group)
        groups_processed = len(list_of_group_titles)

        for phone_number in list_of_phone_numbers:
            users_to_create.append(User(phone_number=phone_number))
        User.objects.bulk_create(users_to_create, ignore_conflicts=True)

        users = User.objects.all().filter(phone_number__in=list_of_phone_numbers)

        groups = Group.objects.all()

        for group in groups:
            for account in group.accounts.all():
                if account.phone_number in list_of_phone_numbers:
                    list_of_phone_numbers.remove(account.phone_number)

        for user in users:
            accounts_to_create.append(Account(user=user, phone_number=user.phone_number, description=None))
        accounts = Account.objects.bulk_create(accounts_to_create, ignore_conflicts=True)

        accounts_created = len(accounts)
        accounts_added = len(list_of_phone_numbers)

        for account in accounts:
            for relation in groups_users_relation:
                if account.phone_number == relation.get('phone_number'):
                    user_group = groups.get(title=relation.get('group'))
                    try:
                        account.groups.add(user_group)
                    except IntegrityError:
                        pass

        return ({
            "message": "OK",
            "counters": {
                "accounts_added": accounts_added,
                "accounts_created": accounts_created,
                "groups_processed": groups_processed,
                "groups_created": groups_created,
            },
            "result": GroupSerializer(instance=Group.objects.all(), many=True).data
        })


class GroupSerializerOnlyAccountsCSV(serializers.ModelSerializer):
    group = serializers.UUIDField(required=True)
    file = serializers.FileField(required=True)

    class Meta:
        model = Group
        fields = ('group', 'file', )

    def create(self, validated_data):
        validate_csv_file_extension(file=validated_data['file'])

        group_id = validated_data.pop('group')
        file = validated_data.pop('file')

        try:
            group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            raise ResponseException('Group not found', status.HTTP_404_NOT_FOUND)

        list_of_phone_numbers = []

        for chunk in list(file.read().splitlines()):
            try:
                try:
                    if validate_phone_number(chunk.decode('utf8').split(',')[0]):
                        list_of_phone_numbers.append(chunk.decode('utf8').split(',')[0])
                except IndexError:
                    if validate_phone_number(chunk.decode('utf8')):
                        list_of_phone_numbers.append(chunk.decode('utf8'))
            except UnicodeDecodeError:
                try:
                    if validate_phone_number(chunk.decode('cp1251').split(',')[0]):
                        list_of_phone_numbers.append(chunk.decode('cp1251').split(',')[0])
                except IndexError:
                    if validate_phone_number(chunk.decode('cp1251')):
                        list_of_phone_numbers.append(chunk.decode('cp1251'))

        for account in group.accounts.all():
            if account.phone_number in list_of_phone_numbers:
                list_of_phone_numbers.remove(account.phone_number)

        users_to_create = []
        accounts_to_create = []

        for phone_number in list_of_phone_numbers:
            users_to_create.append(User(phone_number=phone_number))
        User.objects.bulk_create(users_to_create, ignore_conflicts=True)

        users = User.objects.all().filter(phone_number__in=list_of_phone_numbers)

        for user in users:
            accounts_to_create.append(Account(user=user, phone_number=user.phone_number, description=None))
        accounts = Account.objects.bulk_create(accounts_to_create, ignore_conflicts=True)

        for account in accounts:
            try:
                account.groups.add(group)
            except IntegrityError:
                pass

        return ({
            "message": "OK",
            "counters": {
                "accounts_added": len(list_of_phone_numbers), "accounts_created": len(accounts)
            },
            "result": GroupSerializer(instance=Group.objects.get(id=group_id)).data
        })


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
    users = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), many=True,
                                               required=True, allow_empty=True)

    def validate(self, attrs):
        if attrs['id'].access < 3:
            raise ValidationError(detail="Can't add to this group", code=400)
        return attrs


def base_group_serializer(group: Group):
    return {
        'id': str(group.id),
        'title': group.title,
        'count': group.accounts.count()
    }
