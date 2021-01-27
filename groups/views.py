import csv
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import (GenericAPIView, ListCreateAPIView,
                                     UpdateAPIView, get_object_or_404)
from rest_framework.mixins import (DestroyModelMixin, Response,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   status)
import werkzeug

from core.permissions import IsAdmin, IsAuthenticated
from groups.models import Group
from groups.serializers import (CreateGroupSerializer, GroupSerializer,
                                SwaggerGroupsParametrs, UpdateGroupSerializer,
                                UpdateGroupUsersSerializer, SwaggerImportSingleGroupParametrs)
import io
from users.models import Account, User


def stream_from_file(file: werkzeug.datastructures.FileStorage) -> io.StringIO:
    """
    Takes csv file and returns iostream decoded with right encoding
        :param file:werkzeug.datastructures.FileStorage: file from formdata
    """
    try:
        # first, just try utf8
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    except UnicodeDecodeError:
        # if not, it is 99% cyrillic win 1251
        file.stream.seek(0)
        try:
            stream = io.StringIO(file.stream.read().decode("cp1251"), newline=None)
        except:
            raise
    except:
        return None
    return stream


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


class AccessGroupImportSingleHandler(ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = None
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerImportSingleGroupParametrs)
    def post(self, request, *args, **kwargs):
        print(request.data.get('file'))
        return Response(status=status.HTTP_200_OK)
