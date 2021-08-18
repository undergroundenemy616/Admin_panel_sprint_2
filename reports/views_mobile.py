from smtplib import SMTPException

from django.core.mail import send_mail
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, Response, status

from booking_api_django_new.base_settings import EMAIL_HOST_USER
from core.permissions import IsAuthenticated
from reports.generate_html import generate_attach, generate_html
from reports.models import Report
from reports.serializers_mobile import MobileReportSerializer, MobileRequestDemoSerializer


class MobileReportCreateView(ListModelMixin,
                             GenericAPIView):

    queryset = Report.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = MobileReportSerializer

    def post(self, request, *args, **kwargs):
        request.data['account'] = request.user.account.id
        if not request.data.get('images'):
            request.data['images'] = []
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = [i.path for i in serializer.validated_data.get('images')]
        body = generate_html(body=serializer.validated_data.get('body'),
                             office=serializer.validated_data.get('office'),
                             account=serializer.validated_data.get('account'))
        body = generate_attach(body=body, attachments=attachments)
        try:
            send_mail(message='',
                      from_email=EMAIL_HOST_USER,
                      recipient_list=[serializer.validated_data['office'].service_email],
                      subject=f"[{serializer.validated_data['office'].title}]: {serializer.validated_data['title']}",
                      html_message=body)
        except SMTPException as error:
            return Response({"Error": error.args}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer.validated_data['id_delivered'] = True
        report = serializer.save()
        return Response(serializer.to_representation(report), status=status.HTTP_201_CREATED)


class MobileRequestDemoView(GenericAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = MobileRequestDemoSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.send_email()
        return Response(data={"message": "Email sent"}, status=status.HTTP_200_OK)
