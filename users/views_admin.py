import django_filters
from django.contrib.auth import user_logged_in
from django.core.mail import send_mail
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status, viewsets
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from booking_api_django_new.settings import EMAIL_HOST_USER
from core.pagination import LimitStartPagination
from core.permissions import IsAdmin
from users.filters_admin import AdminUserFilter
from users.models import Account, User
from users.serializers_admin import (AdminCreateOperatorSerializer,
                                     AdminOfficePanelCreateUpdateSerializer,
                                     AdminOfficePanelSerializer,
                                     AdminPasswordChangeSerializer,
                                     AdminPasswordResetSerializer,
                                     AdminServiceEmailViewValidatorSerializer,
                                     AdminUserCreateSerializer,
                                     AdminUserSerializer, AdminLoginSerializer,
                                     AdminPromotionDemotionSerializer)


class AdminOfficePanelViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.filter(office_panels__isnull=False)
    permission_classes = (IsAdmin,)
    serializer_class = AdminOfficePanelSerializer
    pagination_class = LimitStartPagination
    filter_backends = [filters.SearchFilter, ]
    search_fields = ['first_name', 'last_name', 'middle_name', 'user__phone_number', 'user__email',
                     'phone_number', 'email']

    def get_queryset(self):
        if self.request.method == "GET":
            self.queryset = self.queryset.select_related('user', 'office_panels', 'office_panels__office',
                                                         'office_panels__floor').prefetch_related('groups')
        return self.queryset.all()

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT"]:
            return AdminOfficePanelCreateUpdateSerializer
        return self.serializer_class

    def perform_destroy(self, instance):
        instance.user.delete()


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.filter(office_panels__isnull=True)
    permission_classes = (IsAdmin, )
    serializer_class = AdminUserSerializer
    pagination_class = LimitStartPagination
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = AdminUserFilter
    search_fields = ['first_name', 'last_name', 'middle_name', 'user__phone_number', 'user__email',
                     'phone_number', 'email']

    def get_queryset(self):
        if self.request.method == "GET":
            if self.request.query_params.get('group'):
                self.queryset = Account.objects.all()
            self.queryset = self.queryset.select_related('user', 'photo').prefetch_related('groups')
        return self.queryset.all()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        request.data['user'] = instance.user.id
        if request.data['email'] == "":
            request.data['email'] = None
        return super(AdminUserViewSet, self).update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.user.delete()

    def get_serializer_class(self):
        if self.request.method == "POST" and self.request.data.get('operator'):
            return AdminCreateOperatorSerializer
        if self.request.method == "POST":
            return AdminUserCreateSerializer
        return self.serializer_class


class AdminServiceEmailView(GenericAPIView):
    queryset = Account.objects.all()
    permission_classes = [IsAdmin, ]

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'account': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
            'title': openapi.Schema(type=openapi.TYPE_STRING),
            'body': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ))
    def post(self, request, *args, **kwargs):
        serializer = AdminServiceEmailViewValidatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = Account.objects.get(pk=request.data['account'])

        if not account.email:
            return Response({'detail': 'Account has no email specified'}, status=status.HTTP_400_BAD_REQUEST)

        if request.data['body'] and request.data['title']:
            send_mail(
                recipient_list=[account.email],
                from_email=EMAIL_HOST_USER,
                subject=request.data['title'],
                message=''.join(request.data['body']),
            )
        return Response({'message': 'OK'}, status=status.HTTP_201_CREATED)


class AdminPasswordChangeView(GenericAPIView):
    permission_classes = [IsAdmin, ]
    serializer_class = AdminPasswordChangeSerializer

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'old_password': openapi.Schema(type=openapi.TYPE_STRING),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ))
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_logged_in.send(sender=request.user.__class__, user=request.user, request=request)
        token_serializer = TokenObtainPairSerializer()
        token = token_serializer.get_token(user=request.user)
        return Response({
            'message': "OK",
            'access_token': str(token.access_token),
            'refresh_token': str(token)
        }, status=status.HTTP_200_OK)


class AdminPasswordResetView(GenericAPIView):
    serializer_class = AdminPasswordResetSerializer
    permission_classes = (IsAdmin, )

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'account': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        }
    ))
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class AdminLoginView(GenericAPIView):
    serializer_class = AdminLoginSerializer
    queryset = User.objects.all()
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, message = serializer.auth()

        if not user:
            return Response({'detail': message}, status=400)

        user_logged_in.send(sender=user.__class__, user=user, request=request)
        auth_dict = dict()
        token_serializer = TokenObtainPairSerializer()
        token = token_serializer.get_token(user=user)
        auth_dict["refresh_token"] = str(token)
        auth_dict["access_token"] = str(token.access_token)

        return Response(auth_dict, status=200)


class AdminPromotionDemotionView(GenericAPIView):
    permission_classes = (IsAdmin, )
    serializer_class = AdminPromotionDemotionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.change_status()

        return Response({'message': message}, status=status.HTTP_200_OK)
