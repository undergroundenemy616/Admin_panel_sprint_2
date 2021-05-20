from rest_framework import generics

from core.permissions import IsAdmin
from licenses.models import License
from licenses.serializers_admin import AdminLicenseSerializer


class AdminListLicensesView(generics.ListAPIView):
    serializer_class = AdminLicenseSerializer
    queryset = License.objects.all()
    permission_classes = (IsAdmin, )

    def get_queryset(self):
        if self.request.method == "GET":
            if self.request.query_params.get('free'):
                self.queryset = self.queryset.filter(office__isnull=True)
        return self.queryset.all()
