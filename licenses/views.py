from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from licenses.models import License
from licenses.serializers import LicenseSerializer


class ListOffices(APIView):
	permission_classes = [IsAdminUser]
	serializer_class = RoomSerializer

