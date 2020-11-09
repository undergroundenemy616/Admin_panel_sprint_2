from rest_framework.generics import ListCreateAPIView, GenericAPIView, get_object_or_404
from rest_framework.mixins import RetrieveModelMixin, Response, status

from core.permissions import IsAuthenticated, IsAdmin
from groups.models import Group
from groups.serializers import GroupSerializer, CreateGroupSerializer


class ListCreateGroupAPIView(ListCreateAPIView):
    queryset = Group.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = GroupSerializer
    pagination_class = None

    def post(self, request, *args, **kwargs):
        self.serializer_class = CreateGroupSerializer
        return self.create(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.query_params.get('id'):
            group = get_object_or_404(Group, pk=request.query_params.get('id'))
            serializer = self.serializer_class(instance=group)
            return Response(serializer.to_representation(group), status=status.HTTP_200_OK)
        return self.list(self, request, *args, **kwargs)


class RetrieveGroupView(GenericAPIView, RetrieveModelMixin):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAdmin,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
