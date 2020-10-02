from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
# Local imports
from backends.pagination import DefaultPagination
from backends.mixins import FilterListMixin
from room_types.serializers import RoomTypeSerializer, CreateRoomTypeSerializer
from room_types.models import RoomType
from offices.models import Office


# Create your views here.
class ListCreateRoomTypesView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = RoomTypeSerializer
    queryset = RoomType.objects.all()
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser,)

    def post(self, request, *args, **kwargs):
        self.serializer_class = CreateRoomTypeSerializer
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
    # permission_classes = (IsAdminUser,)

    def put(self, request, pk=None, *args, **kwargs):
        self.queryset = RoomType.objects.filter(pre_defined=False)
        if pk not in [room_type.id for room_type in self.queryset]:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return self.update(request, *args, **kwargs)

    def delete(self, request, pk=None, *args, **kwargs):
        self.queryset = RoomType.objects.filter(pre_defined=False)
        if pk not in [room_type.id for room_type in self.queryset]:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return self.destroy(request, *args, **kwargs)
