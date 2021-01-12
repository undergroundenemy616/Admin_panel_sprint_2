from core.permissions import IsAuthenticated, IsAdmin
from core.pagination import DefaultPagination
from rest_framework.generics import GenericAPIView, get_object_or_404
from rooms.models import RoomMarker
from floors.models import Floor, FloorMap
from floors.serializers import (
    NestedFloorSerializer,
    FloorMapSerializer, FloorSerializer, DetailFloorSerializer, EditFloorSerializer
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

    def get(self, request, *args, **kwargs):
        """Returns list of floors."""
        if request.query_params.get('office'):
            floors_by_office = Floor.objects.filter(office=request.query_params.get('office'))
            if request.query_params.get("type"):
                floors_by_office = Floor.objects.filter(office=request.query_params.get('office'),
                                                        rooms__type__title=request.query_params.get('type'))
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

    def delete(self, request, *args, **kwargs):
        room_markers = RoomMarker.objects.filter(room__floor_id=request.data['floor'])
        if room_markers:
            for marker in room_markers:
                marker.delete()
        floor_instance = get_object_or_404(Floor, pk=request.data['floor'])
        serializer = self.serializer_class(instance=floor_instance)
        return Response(serializer.to_representation(floor_instance), status=status.HTTP_200_OK)
