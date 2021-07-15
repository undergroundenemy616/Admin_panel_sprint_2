
# Create your views here.
from rest_framework import viewsets

from core.permissions import IsAuthenticated
from teams.models import Team
from teams.serializers_mobile import MobileTeamCreateUpdateSerializer, MobileTeamLiteSerializer


class MobileTeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = MobileTeamLiteSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MobileTeamCreateUpdateSerializer
        elif self.request.method == 'PUT':
            return MobileTeamCreateUpdateSerializer
        return self.serializer_class

    def get_queryset(self):
        if self.request.method == 'GET':
            self.queryset = self.queryset.filter(creator=self.request.user.account.id).prefetch_related('users')
        return self.queryset
