from backends.pagination import DefaultPagination
from tables.models import Table
from tables.serializers import TableSerializer
from rest_framework.viewsets import ModelViewSet


class TableView(ModelViewSet):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser, )  # TODO
