import csv
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import (GenericAPIView, ListCreateAPIView,
                                     UpdateAPIView, get_object_or_404)
from rest_framework.mixins import (DestroyModelMixin, Response,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   status)
from rest_framework.parsers import MultiPartParser, FormParser


from core.permissions import IsAdmin, IsAuthenticated
from groups.models import Group
from groups.serializers import (CreateGroupSerializer, GroupSerializer,
                                SwaggerGroupsParametrs, UpdateGroupSerializer,
                                UpdateGroupUsersSerializer, GroupSerializerCSV,
                                GroupSerializerWithAccountsCSV, GroupSerializerOnlyAccountsCSV)
from users.models import Account, User


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
    parser_classes = (MultiPartParser,)

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.FILES)
        serializer.is_valid(raise_exception=True)
        group = get_object_or_404(Group, id=serializer.data['id'])
        group.accounts.set(Account.objects.filter(id__in=serializer.data['users']))
        return Response(GroupSerializer(instance=group).data, status=status.HTTP_200_OK)


class ListCreateGroupCsvAPIView(GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializerCSV
    pagination_class = None
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        groups = serializer.save()
        response = GroupSerializer(instance=groups, many=True).data
        return Response(response, status=status.HTTP_201_CREATED)


class ListCreateGroupWithAccountsCsvAPIView(GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializerWithAccountsCSV
    pagination_class = None
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        groups = serializer.save()
        response = GroupSerializer(instance=groups, many=True).data
        return Response(response, status=status.HTTP_201_CREATED)


class ListCreateGroupOnlyAccountsCsvAPIView(GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializerOnlyAccountsCSV
    pagination_class = None
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        response = GroupSerializer(instance=group).data
        return Response(response, status=status.HTTP_201_CREATED)
