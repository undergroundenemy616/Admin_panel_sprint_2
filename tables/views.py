from rest_framework.permissions import AllowAny
from core.pagination import DefaultPagination
from tables.models import Table, TableTag
from tables.serializers import TableSerializer, TableTagSerializer
from rest_framework.viewsets import ModelViewSet


class TableView(ModelViewSet):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (AllowAny, )  # TODO
    

class TableTagView(ModelViewSet):
    serializer_class = TableTagSerializer
    queryset = TableTag.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (AllowAny, )
