from rest_framework.generics import ListCreateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import RetrieveModelMixin
from groups.models import Group
from groups.serializers import GroupSerializer


class ListCreateGroupAPIView(ListCreateAPIView):
    queryset = Group.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = GroupSerializer
    pagination_class = None


class RetrieveGroupView(GenericAPIView, RetrieveModelMixin):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
