from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, UpdateModelMixin)
from rest_framework.response import Response

# Local imports
from core.pagination import DefaultPagination
from core.permissions import IsAdmin, IsAdminOrReadOnly, IsAuthenticated
from offices.models import Office
from room_types.models import RoomType
from room_types.serializers import (CreateUpdateRoomTypeSerializer,
                                    DestroyRoomTypeSerializer,
                                    RoomTypeSerializer,
                                    SwaggerRoomTypeParametrs)


# Create your views here.
class ListCreateRoomTypesView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = CreateUpdateRoomTypeSerializer
    queryset = RoomType.objects.all()
    pagination_class = None
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAdmin, )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_type = serializer.save(data=request.data)
        return Response(serializer.to_representation(created_type), status=status.HTTP_201_CREATED)

    @swagger_auto_schema(query_serializer=SwaggerRoomTypeParametrs)
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
    permission_classes = (IsAdmin, )

    def put(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(RoomType, pk=pk)
        if not instance.is_deletable:
            return Response({"detail": "Not accepted"}, status=status.HTTP_400_BAD_REQUEST)
        request.data['office'] = instance.office.id
        serializer = self.serializer_class(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.to_representation(instance=instance), *args, **kwargs)

    def delete(self, request, pk=None, *args, **kwargs):
        instance_type = get_object_or_404(RoomType, pk=pk)
        if not instance_type.is_deletable:
            return Response({"detail": "Not accepted"}, status=status.HTTP_400_BAD_REQUEST)
        request.data['type'] = instance_type.id
        self.serializer_class = DestroyRoomTypeSerializer
        serializer = self.serializer_class(data=request.data, instance=instance_type)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.destroy(request, *args, **kwargs)
