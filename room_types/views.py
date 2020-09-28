from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
# Local imports
from backends.pagination import DefaultPagination
from backends.mixins import FilterListMixin
from room_types.serializers import RoomTypeSerializer
from room_types.models import RoomType
from offices.models import Office


# Create your views here.
class ListCreateRoomTypesView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = RoomTypeSerializer
    queryset = RoomType.objects.all()
    pagination_class = DefaultPagination

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.queryset = RoomType.objects.filter(office=get_object_or_404(Office, pk=request.query_params.get('office')))
        return self.list(request, *args, **kwargs)


class UpdateDestroyRoomTypesView(GenericAPIView,
                                 UpdateModelMixin,
                                 DestroyModelMixin):
    serializer_class = RoomTypeSerializer
    queryset = RoomType.objects.all()
    pagination_class = DefaultPagination

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
