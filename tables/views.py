from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, \
    ListModelMixin, Response, status

from core.permissions import IsAuthenticated, IsAdmin
from core.pagination import DefaultPagination
from offices.models import Office
from tables.models import Table, TableTag, Rating
from tables.serializers import TableSerializer, TableTagSerializer, CreateTableSerializer, UpdateTableSerializer, \
    UpdateTableTagSerializer, BaseTableTagSerializer, SwaggerTableParameters
from rest_framework.viewsets import ModelViewSet


class TableView(ListModelMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SwaggerTableParameters)
    def get(self, request, *args, **kwargs):
        response = []
        tables = self.queryset

        if request.query_params.get('office'):
            tables = tables.filter(room__floor__office_id=request.query_params.get('office'))
        if request.query_params.get('floor'):
            tables = tables.filter(room__floor_id=request.query_params.get('floor'))
        if request.query_params.get('room'):
            tables = tables.filter(room_id=request.query_params.get('room'))
        if request.query_params.get('free'):
            if int(request.query_params.get('free')) == 1:
                tables = tables.filter(is_occupied=False)
            elif int(request.query_params.get('free')) == 0:
                tables = tables.filter(is_occupied=True)

        for table in tables:
            response.append(TableSerializer(instance=table).data)

        if request.query_params.getlist('tags'):
            tables_with_the_right_tags = []

            for table in response:
                for tag in table['tags']:
                    if tag['title'] in request.query_params.getlist('tags'):
                        tables_with_the_right_tags.append(table)

            response = list({r['id']: r for r in tables_with_the_right_tags}.values())

        for table in response:
            table['ratings'] = Rating.objects.filter(table_id=table['id']).count()

        response_dict = {
            'results': response
        }
        return Response(response_dict, status=status.HTTP_200_OK)

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
