from rest_framework import serializers, status

from core.handlers import ResponseException
from teams.models import Team
from users.models import Account


class MobileAccountForTeamsSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    firstname = serializers.CharField(source='first_name', allow_blank=True, allow_null=True)
    lastname = serializers.CharField(source='last_name', allow_blank=True, allow_null=True)
    middlename = serializers.CharField(source='middle_name', allow_blank=True, allow_null=True)

    def to_representation(self, instance):
        response = super(MobileAccountForTeamsSerializer, self).to_representation(instance)
        response['phone_number'] = instance.user.phone_number
        response['email'] = instance.user.email
        return response


class MobileTeamBaseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    users = MobileAccountForTeamsSerializer(many=True)
    number = serializers.IntegerField()

    def to_representation(self, instance):
        response = super(MobileTeamBaseSerializer, self).to_representation(instance)
        response['creator'] = instance.creator.id
        response['users'].append(MobileAccountForTeamsSerializer(instance.creator).data)
        return response


class MobileTeamLiteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    creator = MobileAccountForTeamsSerializer()
    title = serializers.CharField()
    number = serializers.IntegerField()


class MobileTeamCreateUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=200, required=True)
    users = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Account.objects.all()), required=False, allow_null=False, max_length=150, min_length=2)

    class Meta:
        model = Team
        fields = ['title', 'users']

    def create(self, validated_data):
        user_existing_teams = Team.objects.filter(creator=self.context['request'].user.account.id)
        if len(user_existing_teams) >= 15:
            return ResponseException("Max limit of teams", status.HTTP_400_BAD_REQUEST)
        new_team = self.Meta.model.objects.create(creator=self.context['request'].user.account,
                                                  title=self.validated_data['title'],
                                                  number=len(self.validated_data['users']) + 1)
        new_team.users.set(self.validated_data['users'])
        return new_team

    def update(self, instance, validated_data):
        instance.number = len(validated_data['users']) + 1
        return super(MobileTeamCreateUpdateSerializer, self).update(instance, validated_data)

    def to_representation(self, instance):
        response = MobileTeamBaseSerializer(instance).data
        return response

