from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
# Local imports
from backends.pagination import DefaultPagination
from bookings.models import Booking
from bookings.serializers import BookingSerializer, BookingForActionSerializer


# Create your views here.
class ListCreateBookingsView(GenericAPIView, CreateModelMixin, ListModelMixin):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    pagination_class = DefaultPagination

    def post(self, request, *args, **kwargs):
        pass

    def get(self, request, *args, **kwargs):
        pass


class ActionActivateBookingsView(GenericAPIView):
    pass


class ActionDeactivateBookingsView(GenericAPIView):
    pass


class ActionEndBookingsView(GenericAPIView):
    pass

