from django.contrib.auth import user_logged_in
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (TokenObtainPairSerializer,
                                                  TokenRefreshSerializer)

from booking_api_django_new.settings.base import (HARDCODED_PHONE_NUMBER,
                                                  HARDCODED_SMS_CODE, SMS_MOCK_CONFIRM)
from core.pagination import LimitStartPagination
from core.permissions import IsAdmin, IsAuthenticated
from users.models import Account, User
from users.registration import confirm_code, send_code
from users.serializers import SwaggerAccountParametr
from users.serializers_mobile import (MobilePasswordChangeSerializer, MobilePasswordResetSetializer,
                                      MobileUserLoginSerializer, MobileUserRegisterSerializer,
                                      MobileSelfUpdateSerializer, MobileConformationSerializer,
                                      MobileContactCheckSerializer, MobileCheckAvailableSerializer)
from users.serializers_mobile import (MobileAccountSerializer,
                                      MobileAccountUpdateSerializer,
                                      MobileEntranceCollectorSerializer,
                                      MobileLoginOrRegisterSerializer,
                                      MobileAccountMeetingSearchSerializer)


class MobileEntranceCollectorView(GenericAPIView):
    serializer_class = MobileEntranceCollectorSerializer
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OK",
                         "email": bool(request.user.email) and bool(request.user.password)}, status=status.HTTP_200_OK)


class OlegView(mixins.ListModelMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = MobileLoginOrRegisterSerializer
    authentication_classes = []

    def get(self, request):
        data = {"oleg": "molodec"}
        return Response(data=data, status=status.HTTP_200_OK)

class MobileLoginOrRegisterUserFromMobileView(mixins.ListModelMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = MobileLoginOrRegisterSerializer
    authentication_classes = []

    def post(self, request):
        """Register or login view"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.data.get('phone', None)
        sms_code = serializer.data.pop('code', None)

        user, created = User.objects.get_or_create(phone_number=phone_number)
        account, account_created = Account.objects.get_or_create(user=user)
        try:
            data = {}
            if not sms_code:  # Register or login user
                if SMS_MOCK_CONFIRM != 'True':
                    send_code(user, created)
                else:
                    print('SMS service is off, any code is acceptable')
                # Creating data for response
                data = {
                    'message': "OK",
                    'new_code_in': 60,
                    'expires_in': 60,
                }
            elif sms_code:  # Confirm code  and user.is_active
                if SMS_MOCK_CONFIRM != 'True':
                    # Confirmation code
                    if phone_number == HARDCODED_PHONE_NUMBER and int(sms_code) == HARDCODED_SMS_CODE:
                        pass
                    else:
                        confirm_code(phone_number, sms_code)
                else:
                    print('SMS service is off, any code is acceptable')

                user_logged_in.send(sender=user.__class__, user=user, request=request)

                serializer = TokenObtainPairSerializer()
                token = serializer.get_token(user=user)
                data = dict()
                data["refresh_token"] = str(token)
                data["access_token"] = str(token.access_token)
                data["account"] = account.id
                data["activated"] = account.user.is_active
            else:
                raise ValueError('Invalid data!')
        except ValueError as error:
            return Response({'detail': str(error), 'message': 'ERROR'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)


class MobileRefreshTokenView(GenericAPIView):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({"detail": "Refresh parameter is required"}, status=400)
        refresh_ser = TokenRefreshSerializer(data=request.data)
        try:
            refresh_ser.is_valid(raise_exception=True)
        except TokenError as e:
            return Response(data={"detail": 'Refresh ' + ''.join(*e.args).lower()}, status=400)
        auth_dict = dict()
        auth_dict["refresh_token"] = str(refresh_ser.validated_data['refresh'])
        auth_dict["access_token"] = str(refresh_ser.validated_data['access'])
        return Response(auth_dict, status=200)


class MobileAccountView(GenericAPIView):
    serializer_class = MobileAccountSerializer
    queryset = Account.objects.all().select_related('user', 'photo').prefetch_related('groups')
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(query_serializer=SwaggerAccountParametr)
    def get(self, request, *args, **kwargs):
        account_id = request.query_params.get('id')
        if not account_id:
            user_id = request.user.id
            account_instance = get_object_or_404(Account, user=user_id)
        else:
            account_instance = get_object_or_404(Account, pk=account_id)
        serializer = self.serializer_class(instance=account_instance)
        return Response(serializer.to_representation(instance=account_instance), status=status.HTTP_200_OK)


class MobileSingleAccountView(GenericAPIView, mixins.DestroyModelMixin):
    serializer_class = MobileAccountUpdateSerializer
    queryset = Account.objects.all().select_related('user', 'photo').prefetch_related('groups')
    permission_classes = (IsAdmin,)

    def put(self, request, pk=None, *args, **kwargs):
        account = get_object_or_404(Account, pk=pk)
        serializer = self.serializer_class(data=request.data, instance=account)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)


class MobileFirstCheckView(GenericAPIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-WORKSPACE'):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class MobileUserRegisterView(GenericAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = MobileUserRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        response = serializer.register()
        return Response(data=response, status=status.HTTP_200_OK)


class MobileUserLoginView(GenericAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = MobileUserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        response = serializer.data
        return Response(data=response, status=status.HTTP_200_OK)


class MobilePasswordChangeView(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = MobilePasswordChangeSerializer

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
        return Response(serializer.data, status=status.HTTP_200_OK)


class MobilePasswordResetView(GenericAPIView):
    serializer_class = MobilePasswordResetSetializer
    permission_classes = []
    authentication_classes = []

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        }
    ))
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        response = serializer.reset()
        return Response(data=response, status=status.HTTP_200_OK)


class MobileConformationView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MobileConformationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        if request.data.get('code'):
            response = serializer.confirm()
        else:
            response = serializer.send_code()
        return Response(data=response, status=status.HTTP_200_OK)


class MobileAccountMeetingSearchView(ListAPIView):
    serializer_class = MobileAccountMeetingSearchSerializer
    queryset = Account.objects.all().select_related('user')
    pagination_class = LimitStartPagination
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'user__phone_number', 'user__email']
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).exclude(user_id=request.user.id)

        if request.query_params.getlist('exclude'):
            queryset = queryset.filter(~Q(id__in=request.query_params.getlist('exclude')))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MobileAccountMeetingSearchSerializer(instance=queryset, data=request.query_params, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MobileSelfView(GenericAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = MobileSelfUpdateSerializer

    def get(self, request, *args, **kwargs):
        return Response(self.serializer_class(instance=request.user).data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request}, instance=request.user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class MobileContactCheckView(GenericAPIView,
                             CreateModelMixin):
    serializer_class = MobileContactCheckSerializer
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MobileCheckAvailableView(GenericAPIView):
    serializer_class = MobileCheckAvailableSerializer
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.check(), status=status.HTTP_200_OK)

