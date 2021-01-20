from drf_yasg.utils import swagger_auto_schema
from core.permissions import IsAuthenticated, IsAdmin
from core.pagination import DefaultPagination
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView, get_object_or_404
from offices.models import Office
from rooms.models import RoomMarker
from floors.models import Floor, FloorMap
from floors.serializers import (
    NestedFloorSerializer,
    FloorMapSerializer, FloorSerializer, DetailFloorSerializer, EditFloorSerializer, SwaggerFloorParameters
)
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin, Response, status
)


class ListCreateFloorView(ListModelMixin,
                          CreateModelMixin,
                          GenericAPIView):
    """Floors API View."""
    queryset = Floor.objects.all()
    pagination_class = None
    serializer_class = NestedFloorSerializer
    # permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        """Create new floor."""
        self.permission_classes = (IsAdmin, )
        if not isinstance(request.data['title'], list):
            request.data['title'] = [request.data['title']]
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        floors = serializer.save()
        return Response(serializer.to_representation(floors), status=status.HTTP_201_CREATED)

    @swagger_auto_schema(query_serializer=SwaggerFloorParameters)
    def get(self, request, *args, **kwargs):
        """Returns list of floors."""

        if request.query_params.get('office'):
            if Office.objects.filter(id=request.query_params.get('office')):
                floors_by_office = self.queryset.all().filter(office=request.query_params.get('office'))
            else:
                return Response({"message": "Office not found"}, status=status.HTTP_404_NOT_FOUND)

            if request.query_params.get('type'):
                floors_by_office = floors_by_office.filter(rooms__type__title=request.query_params.get('type'))

            if int(request.query_params.get('expand')) == 0:
                response = []
                for floor in floors_by_office:
                    serialized_floor = DetailFloorSerializer(instance=floor).data
                    serialized_floor.pop('floor_map')
                    response.append(serialized_floor)
                return Response(response, status=status.HTTP_200_OK)

            self.queryset = floors_by_office
        return self.list(request, *args, **kwargs)


class RetrieveUpdateDeleteFloorView(UpdateModelMixin,
                                    RetrieveModelMixin,
                                    DestroyModelMixin,
                                    GenericAPIView):
    """Detail Floor API View"""
    queryset = Floor.objects.all()
    serializer_class = DetailFloorSerializer
    permission_classes = (IsAdmin,)

    def put(self, request, *args, **kwargs):
        request.data['title'] = [request.data['title']]
        self.serializer_class = EditFloorSerializer
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.permission_classes = (IsAuthenticated, )
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ListCreateDeleteFloorMapView(ListModelMixin,
                                   CreateModelMixin,
                                   DestroyModelMixin,
                                   GenericAPIView):
    """Floor Maps View."""
    queryset = FloorMap.objects.all()
    permission_classes = (IsAdmin, )
    pagination_class = DefaultPagination
    serializer_class = FloorMapSerializer

    def get(self, request, *args, **kwargs):
        self.permission_classes = (IsAuthenticated, )
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'floor': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        }
    ))
    def delete(self, request, *args, **kwargs):
        floormap_instance = FloorMap.objects.filter(floor=request.data['floor']).first()
        floormap_instance.delete()
        floor_instance = get_object_or_404(Floor, pk=request.data['floor'])
        self.serializer_class = FloorSerializer
        serializer = self.serializer_class(instance=floor_instance)
        return Response(serializer.to_representation(floor_instance), status=status.HTTP_200_OK)


class CleanFloorMapView(GenericAPIView):
    queryset = RoomMarker.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsAdmin, ]

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'floor': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        }
    ))
    def delete(self, request, *args, **kwargs):
        room_markers = RoomMarker.objects.filter(room__floor_id=request.data['floor'])
        if room_markers:
            for marker in room_markers:
                marker.delete()
        floor_instance = get_object_or_404(Floor, pk=request.data['floor'])
        serializer = self.serializer_class(instance=floor_instance)
        return Response(serializer.to_representation(floor_instance), status=status.HTTP_200_OK)
