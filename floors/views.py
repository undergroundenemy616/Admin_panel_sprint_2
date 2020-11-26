from rest_framework.permissions import AllowAny
from core.pagination import DefaultPagination
from rest_framework.generics import GenericAPIView
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
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = NestedFloorSerializer

    def post(self, request, *args, **kwargs):
        """Create new floor."""
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
    permission_classes = (AllowAny,)
    serializer_class = DetailFloorSerializer

    def put(self, request, *args, **kwargs):
        request.data['title'] = [request.data['title']]
        self.serializer_class = EditFloorSerializer
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ListCreateDeleteFloorMapView(ListModelMixin,
                                   CreateModelMixin,
                                   DestroyModelMixin,
                                   GenericAPIView):
    """Floor Maps View."""
    queryset = FloorMap.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = DefaultPagination
    serializer_class = FloorMapSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
