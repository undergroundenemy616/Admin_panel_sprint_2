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
        users_in_group = User.objects.filter(account__groups=response['id']).values_list('account__id', flat=True)
        response['count'] = len(users_in_group)
        response['users'] = users_in_group
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

        group_ids = []
        for g in group:
            group_ids.append(g.id)

        groups_processed = len(list_of_group_titles)

        for phone_number in list_of_phone_numbers:
            users_to_create.append(User(phone_number=phone_number))
        User.objects.bulk_create(users_to_create, ignore_conflicts=True)

        users = User.objects.all().filter(phone_number__in=list_of_phone_numbers)

        groups = Group.objects.all()
        groups_created = groups.filter(id__in=group_ids).count()

        for g in groups:
            for account in g.accounts.all():
                if account.phone_number in list_of_phone_numbers:
                    list_of_phone_numbers.remove(account.phone_number)

        for user in users:
            accounts_to_create.append(Account(user=user, phone_number=user.phone_number, description=None))
        accounts = Account.objects.bulk_create(accounts_to_create, ignore_conflicts=True)

        acc_ids = []
        for acc_id in accounts:
            acc_ids.append(acc_id.id)

        accounts_created = Account.objects.filter(id__in=acc_ids).count()
        accounts_added = 0

        accounts = Account.objects.filter(phone_number__in=list_of_phone_numbers)

        for account in accounts:
            for relation in groups_users_relation:
                if account.phone_number == relation.get('phone_number'):
                    user_group = groups.get(title=relation.get('group'))
                    if user_group not in account.groups.all():
                        account.groups.add(user_group)
                        accounts_added += 1

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
        account_data = []

        for chunk in list(file.read().splitlines()):
            if len(chunk) <= 15:
                try:
                    try:
                        if validate_phone_number(chunk.decode('utf8').split(',')[0]):
                            for account in group.accounts.all():
                                if account.phone_number != chunk.decode('utf8').split(',')[0]:
                                    account_data.append(chunk.decode('utf8').split(',')[0])
                                    list_of_phone_numbers.append(chunk.decode('utf8').split(',')[0])
                    except IndexError:
                        if validate_phone_number(chunk.decode('utf8')):
                            for account in group.accounts.all():
                                if account.phone_number != chunk.decode('utf8'):
                                    account_data.append(chunk.decode('utf8'))
                                    list_of_phone_numbers.append(chunk.decode('utf8'))
                except UnicodeDecodeError:
                    try:
                        if validate_phone_number(chunk.decode('cp1251').split(',')[0]):
                            for account in group.accounts.all():
                                if account.phone_number != chunk.decode('cp1251').split(',')[0]:
                                    account_data.append(chunk.decode('cp1251').split(',')[0])
                                    list_of_phone_numbers.append(chunk.decode('cp1251').split(',')[0])
                    except IndexError:
                        if validate_phone_number(chunk.decode('cp1251')):
                            for account in group.accounts.all():
                                if account.phone_number != chunk.decode('cp1251'):
                                    account_data.append(chunk.decode('cp1251'))
                                    list_of_phone_numbers.append(chunk.decode('cp1251'))
            else:
                try:
                    try:
                        if validate_phone_number(chunk.decode('utf8').split(';')[2]):
                            for account in group.accounts.all():
                                if account.phone_number != chunk.decode('utf8').split(';')[2]:
                                    account_data.append({
                                        "full_name": chunk.decode('utf8').split(';')[0],
                                        "email": chunk.decode('utf8').split(';')[1],
                                        "phone_number": chunk.decode('utf8').split(';')[2]
                                    })
                                    list_of_phone_numbers.append(chunk.decode('utf8').split(';')[2])
                    except IndexError:
                        raise ResponseException("Incorrect data format")
                except UnicodeDecodeError:
                    try:
                        if validate_phone_number(chunk.decode('cp1251').split(';')[2]):
                            for account in group.accounts.all():
                                if account.phone_number != chunk.decode('cp1251').split(';')[2]:
                                    account_data.append({
                                        "full_name": chunk.decode('cp1251').split(';')[0],
                                        "email": chunk.decode('cp1251').split(';')[1],
                                        "phone_number": chunk.decode('cp1251').split(';')[2]
                                    })
                                    list_of_phone_numbers.append(chunk.decode('cp1251').split(';')[2])
                    except IndexError:
                        raise ResponseException("Incorrect data format")

        users_to_create = []
        accounts_to_create = []

        for data in account_data:
            if type(data) is dict:
                users_to_create.append(User(phone_number=data.get('phone_number'),
                                            email=data.get('email')))
            else:
                users_to_create.append(User(phone_number=data))
        User.objects.bulk_create(users_to_create, ignore_conflicts=True)

        users = User.objects.all().filter(phone_number__in=list_of_phone_numbers)

        for user in users:
            for data in account_data:
                if type(data) is dict and user.email == data.get('email'):
                    accounts_to_create.append(Account(user=user, phone_number=user.phone_number,
                                                      last_name=data.get('full_name').split(' ')[0],
                                                      first_name=data.get('full_name').split(' ')[1],
                                                      middle_name=data.get('full_name').split(' ')[2],
                                                      email=user.email))
            else:
                accounts_to_create.append(Account(user=user, phone_number=user.phone_number, description=None))
        accounts = Account.objects.bulk_create(accounts_to_create, ignore_conflicts=True)

        acc_ids = []
        for acc_id in accounts:
            acc_ids.append(acc_id.id)

        accounts_added = 0
        accounts_created = Account.objects.filter(id__in=acc_ids).count()

        accounts = Account.objects.filter(phone_number__in=list_of_phone_numbers)

        for account in accounts:
            try:
                account.groups.add(group)
                accounts_added += 1
            except IntegrityError:
                pass

        return ({
            "message": "OK",
            "counters": {
                "accounts_added": accounts_added, "accounts_created": accounts_created
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

    def validate(self, attrs):
        if attrs.get('title'):
            if Group.objects.filter(title=attrs['title']).exclude(pk=self.instance.pk).exists():
                raise ValidationError(detail={"detail": "Group with this title already exists"}, code=400)
        return attrs

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
        if attrs['id'].access < 2:
            raise ValidationError(detail="Can't add to this group", code=400)
        return attrs


def base_group_serializer(group: Group):
    return {
        'id': str(group.id),
        'title': group.title,
        'count': group.accounts.count()
    }
