from typing import Dict, Optional
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from core.pagination import DefaultPagination
from core.mixins import FilterListMixin
from rooms.models import Room
from rooms.serializers import RoomSerializer, FilterRoomSerializer


class RoomsView(FilterListMixin,
                CreateModelMixin,
                GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser,)

    @staticmethod
    def get_mapped_query(request: Request) -> Optional[Dict]:
        """Returns mapped literals for search in database or None."""
        serializer = FilterRoomSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query_params = serializer.data
        mapped = {"floor_id": query_params.get('floor'),
                  "type": query_params.get('type'),
                  "tables__tags__title__in": query_params.get('tags')}
        items = []
        for field in mapped.keys():
            if not mapped[field]:
                items.append(field)
        for item in items:
            del mapped[item]
        return mapped

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DetailRoomView(RetrieveModelMixin,
                     UpdateModelMixin,
                     DestroyModelMixin,
                     GenericAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    pagination_class = DefaultPagination

    # permission_classes = (IsAdminUser,)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


#     mapped = self.get_mapped_query(request)
#     print(mapped)
#     print('Subquery')
#     # counts = Count(Table.objects.filter(is_occupied=True))
#     tables_count = Table.objects.filter(is_occupied=True).annotate(c=Count('*')).values('c')
#     records = Room.objects.annotate(occupied=Subquery(tables_count))
#     # records = Room.objects.annotate(occupied=Count('*', Table.objects.filter(is_occupied=True).count()))
#     print(records)

# mapped = self.get_mapped_query(request)
# is_exists = Floor.objects.filter(pk=mapped['floor_id'])
# rooms = Room.objects.all().filter(floor_id=1)
# tables = Table.objects.all().filter(room_id__in=[r.id for r in rooms])
