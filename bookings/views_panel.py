from datetime import datetime, timezone

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bookings.models import Booking
from bookings.serializers import BookingSerializer
from core.permissions import IsAdmin
from users.models import OfficePanelRelation


class PanelSingleBookingView(GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingSerializer

    def get(self, request, *args, **kwargs):
        try:
            panel = OfficePanelRelation.objects.get(request.user.account.id)
        except OfficePanelRelation.DoesNotExist:
            return Response('Panel not found', status=status.HTTP_404_NOT_FOUND)
        if request.query_params.get('date'):
            try:
                current_date = datetime.strptime(request.query_params.get('date'), '%Y-%m-%d')
            except Exception as e:
                return Response(f'{e} error occured', status=status.HTTP_400_BAD_REQUEST)
        else:
            current_date = datetime.utcnow().replace(tzinfo=timezone.utc)
        existing_booking = Booking.objects.filter(table=panel.room.tables.all(), date_from=current_date)
        return Response(BookingSerializer(instance=existing_booking, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        context_data = {'device': 'panel',
                        'language': request.headers.get('Language', None)}
        serializer = self.serializer_class(data=request.data, context=context_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
