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
    DestroyModelMixin
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
        return self.create(request, *args, **kwargs)

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


# class ListHandler(ListAPIView):
#     # permission_classes = [IsAdminUser]
#     serializer_class = BaseFloorSerializer
#     queryset = Floor.objects.all()
#
#     def get(self, request, *args, **kwargs):
#         """
#         Get filtered floors
#
#         """
#         serializer = FilterFloorSerializer(data=request.query_params)
#         if serializer.is_valid():
#             filter_dict = {
#                 "rooms__type": serializer.data.get('type'),
#                 "rooms__tables__tags__title__in": serializer.data.get('tags')
#             }
#             floors = Floor.objects.filter(
#                 **{key: val for key, val in filter_dict.items() if val is not None}).distinct()
#         else:
#             floors = self.get_queryset()
#         limit = serializer.data.get('limit') or 20
#         start = serializer.data.get('start') or 1
#         paged_offices = Paginator(floors, limit)
#         results = [BaseFloorSerializer(floor).data for floor in paged_offices.get_page(start)]
#         return Response({
#             "start": start,
#             "limit": limit,
#             "count": len(results),
#             "next": "",
#             "previous": "",
#             "results": results
#         })
