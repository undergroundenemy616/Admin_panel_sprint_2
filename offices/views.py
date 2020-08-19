from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from floors.models import Floor
from offices.models import Office, OfficeImages
from licenses.models import License
from offices.serializers import OfficeSerializer, CreateOfficeSerializer, FilterOfficeSerializer, EditOfficeSerializer
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import status
from rest_framework import filters
from django.core.paginator import Paginator


class ListHandler(ListAPIView):
    # permission_classes = [IsAdminUser]
    serializer_class = OfficeSerializer
    queryset = Office.objects.all()

    # search_fields = ['title']
    # filter_backends = (filters.SearchFilter,)

    def post(self, request):
        """
        Add new office

        """
        serializer = CreateOfficeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kwargs = {key: val for key, val in serializer.validated_data.items()}
        images_id = kwargs.pop('images', [])
        floors_number = kwargs.pop('floors_number', 0)
        office = Office(**kwargs)
        office.save()
        for image_id in images_id:
            image = OfficeImages(image_id=image_id, office=office)
            image.save()
        for i in range(0, floors_number):
            floor = Floor(title=str(i + 1), office=office)
            floor.save()
        return Response(self.serializer_class(office).data, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        """
        Get filtered offices

        """
        serializer = FilterOfficeSerializer(data=request.query_params)
        if serializer.is_valid():
            filter_dict = {
                "floors__rooms__type": serializer.data.get('type'),
                "floors__rooms__tables__tags__title__in": serializer.data.get('tags')
            }
            offices = Office.objects.filter(
                **{key: val for key, val in filter_dict.items() if val is not None}).distinct()
        else:
            offices = self.get_queryset()
        limit = serializer.data.get('limit') or 20
        start = serializer.data.get('start') or 1
        paged_offices = Paginator(offices, limit)
        results = [OfficeSerializer(office).data for office in paged_offices.get_page(start)]
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
    serializer_class = OfficeSerializer
    queryset = Office.objects.all()

    def update(self, request, *args, **kwargs):
        serializer = EditOfficeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = {key: val for key, val in serializer.validated_data.items()}
        self.get_queryset().filter(pk=self.kwargs.get('pk')).update(**params)
        return Response(OfficeSerializer(self.get_object()).data)
