from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import (GenericAPIView, ListCreateAPIView,
                                     get_object_or_404)
from rest_framework.mixins import (DestroyModelMixin, Response,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   status)
from rest_framework.parsers import FormParser, MultiPartParser

from core.permissions import IsAdmin, IsAuthenticated
from groups.models import Group
from groups.serializers import (CreateGroupSerializer, GroupSerializer,
                                GroupSerializerCSV, GroupSerializerLite,
                                GroupSerializerOnlyAccountsCSV,
                                GroupSerializerWithAccountsCSV,
                                SwaggerGroupsParametrs, UpdateGroupSerializer,
                                UpdateGroupUsersSerializer)
from users.models import Account


class ListCreateGroupAPIView(ListCreateAPIView):
    queryset = Group.objects.all().prefetch_related('accounts__user')
    serializer_class = GroupSerializer
    pagination_class = None
    permission_classes = (IsAdmin,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', ]

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        self.serializer_class = CreateGroupSerializer
        return self.create(request, *args, **kwargs)

    @swagger_auto_schema(query_serializer=SwaggerGroupsParametrs)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('id'):
            try:
                group = self.queryset.get(id=request.query_params.get('id'))
            except ObjectDoesNotExist:
                return Response("Group not found", status=status.HTTP_404_NOT_FOUND)
            serializer = self.serializer_class(instance=group)
            return Response(serializer.to_representation(group), status=status.HTTP_200_OK)
        self.serializer_class = GroupSerializerLite
        return self.list(request)


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
        accounts_for_inactive = Account.objects.filter(groups=group).exclude(id__in=serializer.data['users'])
        for account in accounts_for_inactive:
            if account.groups.count() == 1:
                account.user.is_active = False
                account.user.save()
        group.accounts.set(Account.objects.filter(id__in=serializer.data['users']))
        for account in Account.objects.select_related("user").filter(id__in=serializer.data['users']):
            if not account.user.is_active and account.groups:
                account.user.is_active = True
                account.user.save()

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
        return Response(groups, status=status.HTTP_200_OK)


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
        return Response(groups, status=status.HTTP_200_OK)


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
        return Response(group, status=status.HTTP_200_OK)
