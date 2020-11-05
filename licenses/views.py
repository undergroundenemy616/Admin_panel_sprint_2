from rest_framework import status
from rest_framework.generics import ListCreateAPIView, GenericAPIView
from rest_framework.response import Response
from core.pagination import DefaultPagination
from core.permissions import IsAdmin
from licenses.models import License
from licenses.serializers import LicenseSerializer
from offices.models import Office


class ListOffices(ListCreateAPIView):
    serializer_class = LicenseSerializer
    queryset = License.objects.all()
    pagination_class = DefaultPagination
    # permission_classes = (IsAdminUser, )


class ListLicensesView(GenericAPIView):
    serializer_class = LicenseSerializer
    queryset = License.objects.all()
    permission_classes = (IsAdmin,)

    def get(self, request, *args, **kwargs):
        response = []
        licenses = License.objects.all()
        if request.query_params.get('free') == 'true':
            chained_licenses = []
            offices = Office.objects.all()
            for office in offices:
                chained_licenses.append(office.license.id)
            for single_license in licenses:
                if single_license.id not in chained_licenses:
                    response.append(LicenseSerializer(instance=single_license).data)
        else:
            for single_license in licenses:
                response.append(LicenseSerializer(instance=single_license).data)
        return Response(response, status=status.HTTP_200_OK)
