from rest_framework.generics import ListCreateAPIView
from core.pagination import DefaultPagination
from licenses.models import License
from licenses.serializers import LicenseSerializer


class ListOffices(ListCreateAPIView):
    serializer_class = LicenseSerializer
    queryset = License.objects.all()
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser, )
