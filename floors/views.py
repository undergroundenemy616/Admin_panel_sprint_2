from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from floors.models import Floor
from offices.models import Office
from floors.serializers import FloorSerializer, CreateFloorSerializer, FilterFloorSerializer, EditFloorSerializer
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from django.core.paginator import Paginator
from rest_framework import status


class ListHandler(ListAPIView):
    # permission_classes = [IsAdminUser]
    serializer_class = FloorSerializer
    queryset = Floor.objects.all()

    def post(self, request):
        """
        Add new floor

        """
        serializer = CreateFloorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = {key: val for key, val in serializer.validated_data.items()}
        floor = Floor(**params)
        floor.save()
        return Response(self.serializer_class(floor).data, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        """
        Get filtered floors

        """
        serializer = FilterFloorSerializer(data=request.query_params)
        if serializer.is_valid():
            filter_dict = {
                "rooms__type": serializer.data.get('type'),
                "rooms__tables__tags__title__in": serializer.data.get('tags')
            }
            floors = Floor.objects.filter(
                **{key: val for key, val in filter_dict.items() if val is not None}).distinct()
        else:
            floors = self.get_queryset()
        limit = serializer.data.get('limit') or 20
        start = serializer.data.get('start') or 1
        paged_offices = Paginator(floors, limit)
        results = [FloorSerializer(floor).data for floor in paged_offices.get_page(start)]
        return Response({
            "start": start,
            "limit": limit,
            "count": len(results),
            "next": "",
            "previous": "",
            "results": results
        })


class ObjectHandler(RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAdminUser]
    serializer_class = FloorSerializer
    queryset = Floor.objects.all()

    def update(self, request, *args, **kwargs):
        serializer = EditFloorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = {key: val for key, val in serializer.validated_data.items()}
        self.get_queryset().filter(pk=self.kwargs.get('pk')).update(**params)
        return Response(FloorSerializer(self.get_object()).data)
