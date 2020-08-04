from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import AllowAny
from groups.models import Group
from groups.serializers import GroupSerializer


class ListCreateGroupAPIView(ListCreateAPIView):
    queryset = Group.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = GroupSerializer
