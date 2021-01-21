import datetime
from drf_yasg.utils import swagger_auto_schema
from django.core.mail import send_mail
from django.conf.global_settings import EMAIL_HOST_USER
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (CreateModelMixin,
                                   ListModelMixin, Response,
                                   status)

from core.permissions import IsAuthenticated
from report.serializers import ReportSerializer, SwaggerReportParametrs
from report.models import Report
from report.generate_html import generate_html, generate_attach
from users.models import Account, User


class ReportCreateView(ListModelMixin,
                       CreateModelMixin,
                       GenericAPIView):

    queryset = Report.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = ReportSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = [i.path for i in serializer.validated_data['images']]
        body = generate_html(body=serializer.validated_data['body'],
                             office=serializer.validated_data['office'].title,
                             account=serializer.validated_data['account'])
        body = generate_attach(body=body, attachments=attachments)
        send_mail(message='',
                  from_email=EMAIL_HOST_USER,
                  recipient_list=[serializer.validated_data['office'].service_email],
                  subject=f"[{serializer.validated_data['office'].title}]: {datetime.datetime.now()}",
                  html_message=body)
        serializer.validated_data['id_delivered'] = True
        report = serializer.save()
        return Response(serializer.to_representation(report), status=status.HTTP_201_CREATED)

    @swagger_auto_schema(query_serializer=SwaggerReportParametrs)
    def get(self, request, *args, **kwargs):
        query = get_object_or_404(Report, pk=request.data.get('id', ''))
        serializer = self.serializer_class(instance=query)
        return Response(serializer.to_representation(query), status=status.HTTP_200_OK)


class ReportHistoryView(ListModelMixin, GenericAPIView):
    queryset = Report.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = ReportSerializer

    def get(self, request, *args, **kwargs):
        user = User.objects.get(pk=request.user.id)
        account = Account.objects.get(user=user)
        self.queryset = Report.objects.filter(account=account).all()
        return self.list(request, *args, **kwargs)
