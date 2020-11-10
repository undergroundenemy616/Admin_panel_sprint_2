from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
# Local imports
from core.pagination import DefaultPagination
from core.mixins import FilterListMixin
from room_types.serializers import RoomTypeSerializer, CreateUpdateRoomTypeSerializer, DestroyRoomTypeSerializer
from room_types.models import RoomType
from offices.models import Office


# Create your views here.
class ListCreateRoomTypesView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = CreateUpdateRoomTypeSerializer
    queryset = RoomType.objects.all()
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_type = serializer.save(data=request.data)
        return Response(serializer.to_representation(created_type), status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        self.serializer_class = RoomTypeSerializer
        self.queryset = RoomType.objects.filter(office=get_object_or_404(Office, pk=request.query_params.get('office')))
        return self.list(request, *args, **kwargs)


class UpdateDestroyRoomTypesView(GenericAPIView,
                                 UpdateModelMixin,
                                 DestroyModelMixin):
    serializer_class = CreateUpdateRoomTypeSerializer
    queryset = RoomType.objects.filter(is_deletable=True)
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser,)

    def put(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(RoomType, pk=pk)
        if not instance.is_deletable:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        office = Office.objects.filter(id=instance.office.id).first()
        request.data['office'] = office.id
        # Made because i don't want to implement another serializer
        if not request.data.get('title'):
            request.data['title'] = [instance.title]
        else:
            title = request.data.pop('title')
            request.data['title'] = [title]
        serializer = self.serializer_class(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.to_representation(instance=instance), *args, **kwargs)

    def delete(self, request, pk=None, *args, **kwargs):
        instance_type = get_object_or_404(RoomType, pk=pk)
        request.data['type'] = instance_type.id
        self.serializer_class = DestroyRoomTypeSerializer
        serializer = self.serializer_class(data=request.data, instance=instance_type)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.destroy(request, *args, **kwargs)
