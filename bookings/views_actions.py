from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import DestroyModelMixin
from rest_framework.response import Response


from bookings.models import Booking
from bookings.serializers import (BookingActivateActionSerializer,
                                  BookingDeactivateActionSerializer,
                                  BookingSlotsSerializer)
from core.permissions import IsAdmin, IsAuthenticated


class ActionCheckAvailableSlotsView(GenericAPIView):
    serializer_class = BookingSlotsSerializer
    queryset = Booking.objects.all().select_related('table')
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActionActivateBookingsView(GenericAPIView):
    """
    Authenticated User route. Change status of booking.
    """
    serializer_class = BookingActivateActionSerializer
    queryset = Booking.objects.all().select_related('table')
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # request.data['user'] = request.user
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionDeactivateBookingsView(GenericAPIView):
    """
    Admin route. Deactivates any booking
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all().select_related('table')
    permission_classes = (IsAdmin, )

    def post(self, request, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user.account)
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionEndBookingsView(GenericAPIView, DestroyModelMixin):
    """
    User route. Deactivate booking only connected with User
    """
    serializer_class = BookingDeactivateActionSerializer
    queryset = Booking.objects.all().select_related('table')
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        # now = datetime.utcnow().replace(tzinfo=timezone.utc)
        existing_booking = get_object_or_404(Booking, pk=request.data.get('booking'))
        if existing_booking.user.id != request.user.account.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        # booking = serializer.validated_data['booking']
        # if now < booking.date_from and now < booking.date_to:
        #     return self.destroy(request, *args, **kwargs)
        serializer.save()
        return Response(serializer.to_representation(existing_booking), status=status.HTTP_200_OK)


class ActionCancelBookingsView(GenericAPIView):
    """
    User route. Set booking over
    """
    queryset = Booking.objects.all().select_related('table', 'user')
    serializer_class = BookingDeactivateActionSerializer
    permission_classes = (IsAuthenticated, )

    def delete(self, request, pk=None, *args, **kwargs):
        existing_booking = get_object_or_404(Booking, pk=pk)
        user_is_admin = False
        for group in request.user.account.groups.all():
            if group.title == 'Администратор' and not group.is_deletable:
                user_is_admin = True
        if existing_booking.user.id != request.user.account.id and not user_is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)
        request.data['booking'] = existing_booking.id
        serializer = self.serializer_class(data=request.data, instance=existing_booking)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = get_object_or_404(Booking, pk=pk)
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)
