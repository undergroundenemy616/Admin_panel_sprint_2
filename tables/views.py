from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, \
    ListModelMixin, Response, status
from core.permissions import IsAuthenticated, IsAdmin
from core.pagination import DefaultPagination
from offices.models import Office
from tables.models import Table, TableTag
from tables.serializers import TableSerializer, TableTagSerializer, CreateTableSerializer, UpdateTableSerializer, \
    UpdateTableTagSerializer, BaseTableTagSerializer
from rest_framework.viewsets import ModelViewSet


class TableView(ListModelMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        self.serializer_class = CreateTableSerializer
        return self.create(request, *args, **kwargs)


class DetailTableView(RetrieveModelMixin,
                      UpdateModelMixin,
                      DestroyModelMixin,
                      GenericAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    permission_classes = (IsAdmin, )

    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateTableSerializer
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.permission_classes = (IsAuthenticated, )
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class TableTagView(ListModelMixin,
                   CreateModelMixin,
                   GenericAPIView):
    serializer_class = TableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = None
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        # self.serializer_class = ListTableTagSerializer
        # serializer = self.serializer_class(data={'office': request.query_params.get('office')})
        # serializer.is_valid(raise_exception=True)
        self.serializer_class = BaseTableTagSerializer
        self.queryset = TableTag.objects.filter(office_id=get_object_or_404(Office,
                                                                            pk=request.query_params.get('office')))
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        if isinstance(request.data['title'], str):
            request.data['title'] = [request.data['title']]
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_tag = serializer.save()
        return Response(serializer.to_representation(instance=created_tag),
                        status=status.HTTP_201_CREATED)


class DetailTableTagView(GenericAPIView,
                         UpdateModelMixin,
                         DestroyModelMixin):
    serializer_class = TableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAdmin, )

    def put(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(TableTag, pk=pk)
        self.serializer_class = UpdateTableTagSerializer
        serializer = self.serializer_class(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        response = serializer.to_representation(updated)
        return Response(response[0], status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
