from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, \
    ListModelMixin
from rest_framework.permissions import AllowAny
from core.pagination import DefaultPagination
from offices.models import Office
from tables.models import Table, TableTag
from tables.serializers import TableSerializer, TableTagSerializer, CreateTableSerializer, UpdateTableSerializer, \
    UpdateTableTagSerializer, ListTableTagSerializer
from rest_framework.viewsets import ModelViewSet


class TableView(ListModelMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.serializer_class = CreateTableSerializer
        return self.create(request, *args, **kwargs)


class DetailTableView(RetrieveModelMixin,
                      UpdateModelMixin,
                      DestroyModelMixin,
                      GenericAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()

    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateTableSerializer
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class TableTagView(ListModelMixin,
                   CreateModelMixin,
                   GenericAPIView):
    serializer_class = TableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        # self.serializer_class = ListTableTagSerializer
        # serializer = self.serializer_class(data={'office': request.query_params.get('office')})
        # serializer.is_valid(raise_exception=True)
        self.queryset = TableTag.objects.filter(office_id=get_object_or_404(Office,
                                                                            pk=request.query_params.get('office')))
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DetailTableTagView(GenericAPIView,
                         UpdateModelMixin,
                         DestroyModelMixin):
    serializer_class = TableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (AllowAny,)

    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateTableTagSerializer
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
