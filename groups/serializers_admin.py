from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.db.transaction import atomic
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from booking_api_django_new.validate_phone_number import validate_phone_number
from core.handlers import ResponseException
from groups.models import Group
from offices.models import Office, OfficeZone
from users.models import Account, User


def validate_csv_file_extension(file):
    if '.csv' not in str(file):
        raise ValidationError('Unsupported file extension')


class AdminGroupForOfficeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ['id', 'title']

    def to_representation(self, instance):
        response = super(AdminGroupForOfficeSerializer, self).to_representation(instance)
        response['pre_defined'] = not instance.is_deletable
        response['count'] = instance.count if hasattr(instance, 'count') else instance.accounts.count()
        return response


class AdminGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        exclude = ['is_deletable']

    def to_representation(self, instance):
        response = super(AdminGroupSerializer, self).to_representation(instance)
        response['pre_defined'] = not instance.is_deletable
        response['count'] = instance.count if hasattr(instance, 'count') else instance.accounts.count()
        legacy_access = Group.to_legacy_access(access=instance.access)
        if not legacy_access:
            raise serializers.ValidationError('Invalid group access')
        response.update(legacy_access)
        return response


class AdminUserForGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'phone_number', 'description', 'first_name', 'last_name', 'middle_name']

    def to_representation(self, instance):
        response = super(AdminUserForGroupSerializer, self).to_representation(instance)
        if response['phone_number'] == "":
            response['phone_number'] = instance.user.phone_number
        return response


class AdminGroupCreateSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(),
                                               source='accounts', default=[], many=True)
    global_can_manage = serializers.BooleanField(required=True, write_only=True)
    global_can_write = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = Group
        fields = ['title', 'description', 'global_can_manage', 'global_can_write', 'users']

    def validate(self, attrs):
        attrs['access'] = Group.from_legacy_access(
            w=attrs.pop('global_can_write'),
            m=attrs.pop('global_can_manage'),
            s=False
        )
        attrs['is_deletable'] = True
        return attrs

    def to_representation(self, instance):
        return AdminGroupSerializer(instance=instance).data


class AdminGroupUpdateSerializer(serializers.ModelSerializer):
    users_add = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), default=[], many=True)
    users_remove = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), default=[], many=True)
    global_can_manage = serializers.BooleanField(required=False, write_only=True)
    global_can_write = serializers.BooleanField(required=False, write_only=True)
    title = serializers.CharField(required=False)

    class Meta:
        model = Group
        fields = ['title', 'description', 'global_can_manage', 'global_can_write', 'users_add', 'users_remove']

    def validate(self, attrs):
        if attrs.get('global_can_write') and attrs.get('global_can_manage'):
            attrs['access'] = Group.from_legacy_access(
                w=attrs.pop('global_can_write'),
                m=attrs.pop('global_can_manage'),
                s=False
            )

        attrs['users_add'] = set(attrs['users_add'])
        attrs['users_remove'] = set(attrs['users_remove'])

        if attrs['users_add'] and attrs['users_remove']:
            users_in_both = attrs['users_add'] & attrs['users_remove']
            attrs['users_add'] = attrs['users_add'] - users_in_both
            attrs['users_remove'] = attrs['users_remove'] - users_in_both

        return attrs

    @atomic()
    def update(self, instance, validated_data):
        instance.accounts.add(*validated_data['users_add'])
        instance.accounts.remove(*validated_data['users_remove'])
        return super(AdminGroupUpdateSerializer, self).update(instance, validated_data)

    def to_representation(self, instance):
        return AdminGroupSerializer(instance=instance).data


class AdminOfficeForGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeZone
        fields = ['id', 'title']


class AdminZoneForGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'title', 'description']

    def to_representation(self, instance):
        response = super(AdminZoneForGroupSerializer, self).to_representation(instance)
        response['zones'] = AdminOfficeForGroupSerializer(instance=OfficeZone.objects.filter(
            office__id=instance.id, groups__id=self.context['group_id']), many=True).data
        return response


class AdminGroupUserAccessSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ['id', 'title']

    def to_representation(self, instance):
        response = super(AdminGroupUserAccessSerializer, self).to_representation(instance)
        office_zone = instance.groups.values_list('id', flat=True)
        response['offices'] = AdminZoneForGroupSerializer(
            instance=Office.objects.filter(zones__id__in=office_zone).distinct(),
            many=True, context={'group_id': instance.id}).data
        return response


class AdminImportAccountsInGroupCsvSerializer(serializers.Serializer):
    group = serializers.UUIDField(required=True)
    file = serializers.FileField(required=True)

    def create(self, validated_data):
        validate_csv_file_extension(file=validated_data['file'])

        group_id = validated_data.pop('group')
        file = validated_data.pop('file')

        try:
            group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            raise ResponseException('Group not found', status.HTTP_404_NOT_FOUND)

        list_of_phone_numbers = []
        accounts_created = 0

        for chunk in list(file.read().splitlines()):
            try:
                try:
                    try:
                        if validate_phone_number(User.normalize_phone(chunk.decode('utf8').split(',')[0])):
                            list_of_phone_numbers.append(User.normalize_phone(chunk.decode('utf8').split(',')[0]))
                    except ValueError:
                        raise ResponseException("Incorrect data format, check provided example",
                                                status_code=status.HTTP_400_BAD_REQUEST)
                except IndexError:
                    try:
                        if validate_phone_number(User.normalize_phone(chunk.decode('utf8'))):
                            list_of_phone_numbers.append(User.normalize_phone(chunk.decode('utf8')))
                    except ValueError:
                        raise ResponseException("Incorrect data format, check provided example",
                                                status_code=status.HTTP_400_BAD_REQUEST)
            except UnicodeDecodeError:
                try:
                    try:
                        if validate_phone_number(User.normalize_phone(chunk.decode('cp1251').split(',')[0])):
                            list_of_phone_numbers.append(User.normalize_phone(chunk.decode('cp1251').split(',')[0]))
                    except ValueError:
                        raise ResponseException("Incorrect data format, check provided example",
                                                status_code=status.HTTP_400_BAD_REQUEST)
                except IndexError:
                    try:
                        if validate_phone_number(User.normalize_phone(chunk.decode('cp1251'))):
                            list_of_phone_numbers.append(User.normalize_phone(chunk.decode('cp1251')))
                    except ValueError:
                        raise ResponseException("Incorrect data format, check provided example",
                                                status_code=status.HTTP_400_BAD_REQUEST)

        for number in list_of_phone_numbers:
            user = User.objects.get_or_create(phone_number=number)
            account, create = Account.objects.get_or_create(user=user[0])
            if create:
                accounts_created += 1
            account.groups.add(group)

        return ({
            "message": "OK",
            "counters": {
                "accounts_added": len(list_of_phone_numbers), "accounts_created": accounts_created
            },
            "result": AdminGroupSerializer(instance=Group.objects.get(id=group_id)).data
        })


class AdminImportAccountAndGroupsCsvSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def create(self, validated_data):
        validate_csv_file_extension(file=validated_data['file'])

        file = validated_data.pop('file')

        phone_numbers = []
        groups = []

        for chunk in list(file.read().splitlines()):
            try:
                try:
                    if validate_phone_number(User.normalize_phone(chunk.decode('utf8').split(',')[0])):
                        phone_numbers.append(User.normalize_phone(chunk.decode('utf8').split(',')[0]))
                    groups.append(chunk.decode('utf8').split(',')[1])
                except ValueError:
                    raise ResponseException("Incorrect data format, check provided example",
                                            status_code=status.HTTP_400_BAD_REQUEST)
            except UnicodeDecodeError:
                try:
                    if validate_phone_number(User.normalize_phone(chunk.decode('cp1251').split(',')[0])):
                        phone_numbers.append(User.normalize_phone(chunk.decode('cp1251').split(',')[0]))
                    groups.append(chunk.decode('cp1251').split(',')[1])
                except ValueError:
                    raise ResponseException("Incorrect data format, check provided example",
                                            status_code=status.HTTP_400_BAD_REQUEST)

        accounts_created = 0
        groups_created = 0

        for i in range(len(phone_numbers)):
            user = User.objects.get_or_create(phone_number=phone_numbers[i])
            account, created = Account.objects.get_or_create(user=user[0])
            if created:
                accounts_created += 1
            group, created = Group.objects.get_or_create(title=groups[i])
            if created:
                groups_created += 1
            account.groups.add(group)

        groups_processed = len(set(groups))
        accounts_added = len(phone_numbers)

        return ({
            "message": "OK",
            "counters": {
                "accounts_added": accounts_added,
                "accounts_created": accounts_created,
                "groups_processed": groups_processed,
                "groups_created": groups_created,
            },
            "result": AdminGroupSerializer(instance=Group.objects.all().annotate(
                count=Count('accounts')
            ), many=True).data
        })


class AdminCreateGroupCsvSerialzer(serializers.ModelSerializer):
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
            "result": AdminGroupSerializer(instance=Group.objects.all().annotate(
                count=Count('accounts')
            ), many=True).data
        })