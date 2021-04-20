from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.permissions import IsAdmin
from users.models import User
from users.serializers import AccountSerializer
from users.serializers_panel import PanelRegisterUserSerializer


class PanelRegisterUserView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = PanelRegisterUserSerializer
    permission_classes = (IsAdmin, )

    def post(self, request):
        if request.data.get('phone_number'):
            request.data['phone'] = request.data.get('phone_number')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        response = AccountSerializer(instance=account).data
        return Response(response, status=status.HTTP_201_CREATED)
