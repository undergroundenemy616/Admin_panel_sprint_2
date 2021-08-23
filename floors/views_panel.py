from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, Response, status

from core.permissions import IsAdmin
from floors.models import Floor
from floors.serializers import NestedFloorSerializer, SwaggerFloorParameters
from offices.models import Office
from rooms.serializers_panel import PanelFloorSerializerWithMap


class PanelListFloorView(ListModelMixin, GenericAPIView):
    """Floors API View."""
    queryset = Floor.objects.all().prefetch_related('rooms', 'rooms__images',
                                                    'office__zones').select_related('office')
    pagination_class = None
    serializer_class = NestedFloorSerializer
    permission_classes = (IsAdmin, )


    @swagger_auto_schema(query_serializer=SwaggerFloorParameters)
    def get(self, request, *args, **kwargs):
        """Returns list of floors."""
        if request.query_params.get('office'):
            if Office.objects.filter(id=request.query_params.get('office')):
                floors_by_office = self.queryset.all().filter(office=request.query_params.get('office'), rooms__type__unified=True).distinct('id')
            else:
                return Response({"message": "Office not found"}, status=status.HTTP_404_NOT_FOUND)
            response = PanelFloorSerializerWithMap(instance=floors_by_office.prefetch_related('rooms'), many=True).data
            return Response(response, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
