from rest_framework.generics import ListCreateAPIView, GenericAPIView, get_object_or_404, UpdateAPIView
from rest_framework.mixins import RetrieveModelMixin, Response, status, UpdateModelMixin, DestroyModelMixin
from drf_yasg.utils import swagger_auto_schema

from core.permissions import IsAuthenticated, IsAdmin
from groups.models import Group
from groups.serializers import GroupSerializer, CreateGroupSerializer, UpdateGroupSerializer, UpdateGroupUsersSerializer, \
SwaggerGroupsParametrs
from users.models import User, Account


class ListCreateGroupAPIView(ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = None
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        self.serializer_class = CreateGroupSerializer
        return self.create(request, *args, **kwargs)

    @swagger_auto_schema(query_serializer=SwaggerGroupsParametrs)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('id'):
            group = get_object_or_404(Group, pk=request.query_params.get('id'))
            serializer = self.serializer_class(instance=group)
            return Response(serializer.to_representation(group), status=status.HTTP_200_OK)
        return self.list(self, request, *args, **kwargs)


class DetailGroupView(GenericAPIView,
                      UpdateModelMixin,
                      RetrieveModelMixin,
                      DestroyModelMixin):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAdmin,)

    def get(self, request, *args, **kwargs):
        self.permission_classes = (IsAuthenticated, )
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateGroupSerializer
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateUsersGroupView(GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = UpdateGroupUsersSerializer
    permission_classes = (IsAdmin, )

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = get_object_or_404(Group, id=serializer.data['id'])
        group.accounts.set(Account.objects.filter(id__in=serializer.data['users']))
        return Response(GroupSerializer(instance=group).data, status=status.HTTP_200_OK)
