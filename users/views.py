import os
import random
import jwt

import orjson
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from django.http import JsonResponse
from booking_api_django_new.settings import EMAIL_HOST_USER
from django.contrib.auth import user_logged_in
from django.core.mail import send_mail
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, filters
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from booking_api_django_new.settings import HARDCODED_PHONE_NUMBER, HARDCODED_SMS_CODE
from core.authentication import AuthForAccountPut
from core.handlers import ResponseException
from core.pagination import DefaultPagination, LimitStartPagination
from core.permissions import IsAdmin, IsAuthenticated, IsOwner
from groups.models import Group
from mail import send_html_email_message
from users.models import Account, User, OfficePanelRelation
from users.registration import confirm_code, send_code
from users.serializers import (AccountSerializer, AccountUpdateSerializer,
                               LoginOrRegisterSerializer,
                               LoginOrRegisterStaffSerializer,
                               PasswordChangeSerializer,
                               PasswordResetSerializer,
                               RegisterStaffSerializer,
                               RegisterUserFromAPSerializer,
                               SwaggerAccountListParametr,
                               SwaggerAccountParametr, user_access_serializer,
                               EntranceCollectorSerializer, TestAccountSerializer,
                               AccountListGetSerializer, OfficePanelSerializer, LoginOfficePanel)


class RegisterUserFromAdminPanelView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterUserFromAPSerializer
    permission_classes = (IsAdmin, )

    def post(self, request):
        if request.data.get('phone_number'):
            request.data['phone'] = request.data.get('phone_number')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        response = AccountSerializer(instance=account).data
        return Response(response, status=status.HTTP_201_CREATED)


class LoginOrRegisterUserFromMobileView(mixins.ListModelMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = LoginOrRegisterSerializer
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
                if not os.getenv('SMS_MOCK_CONFIRM'):
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
                if not os.getenv('SMS_MOCK_CONFIRM'):
                    # Confirmation code
                    if phone_number == HARDCODED_PHONE_NUMBER and sms_code == HARDCODED_SMS_CODE:
                        pass
                    else:
                        confirm_code(phone_number, sms_code)
                else:
                    print('SMS service is off, any code is acceptable')

                user_logged_in.send(sender=user.__class__, user=user, request=request)

                # Creating data for response
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


def authenticate_staff(request=None, **fields):
    """Returns tuple of (user, None) if authentication credentials correct, otherwise returns (None, message)."""
    try:
        user = User.objects.get(email=fields.get('username'))
    except (User.DoesNotExist, KeyError, TypeError):
        return None, 'Incorrect email or password'

    is_correct = user.check_password(fields.get('password'))
    if not is_correct:
        return None, 'Incorrect email or password'

    if not user.is_staff or not user.is_active:
        return None, 'User is not a staff or has been blocked.'

    return user, None


class LoginStaff(GenericAPIView):
    serializer_class = LoginOrRegisterStaffSerializer
    queryset = User.objects.all()
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, message = authenticate_staff(request, **serializer.validated_data)
        if not user:
            return Response({'detail': message}, status=400)
        # data = dict()
        user_logged_in.send(sender=user.__class__, user=user, request=request)
        auth_dict = dict()
        token_serializer = TokenObtainPairSerializer()
        token = token_serializer.get_token(user=user)
        auth_dict["refresh_token"] = str(token)
        auth_dict["access_token"] = str(token.access_token)
        # data['status'], data['user'] = 'DONE', UserSerializer(instance=user).data
        return Response(auth_dict, status=200)


class LoginOfficePanel(GenericAPIView):
    queryset = User.objects.all()
    authentication_classes = []
    serializer_class = LoginOfficePanel

    def post(self, request, *args, **kwargs):
        access_code = request.data.get('access_code')

        if not access_code:
            raise ResponseException("Invalid Credentials", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            office_panel_info = OfficePanelRelation.objects.get(access_code=access_code)
        except OfficePanelRelation.DoesNotExist:
            raise ResponseException("Data not found", status_code=status.HTTP_404_NOT_FOUND)

        if not office_panel_info.office or not office_panel_info.floor:
            raise ResponseException("Panel has no office/floor", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=office_panel_info.account.user.id)
        except User.DoesNotExist:
            raise ResponseException("Account not found", status_code=status.HTTP_404_NOT_FOUND)

        serializer = TokenObtainPairSerializer()
        token = serializer.get_token(user=user)
        data = dict()
        data["refresh_token"] = str(token)
        data["access_token"] = str(token.access_token)
        data["office"] = str(office_panel_info.office.id)
        data["floor"] = str(office_panel_info.floor.id)

        return Response(data, status=status.HTTP_200_OK)


class AccountView(GenericAPIView):
    serializer_class = AccountSerializer
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


class SingleAccountView(GenericAPIView, mixins.DestroyModelMixin):
    serializer_class = AccountUpdateSerializer
    queryset = Account.objects.all().select_related('user', 'photo').prefetch_related('groups')
    permission_classes = (IsAuthenticated,)

    def put(self, request, pk=None, *args, **kwargs):
        account = get_object_or_404(Account, pk=pk)
        if account.id != request.user.account.id and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data, instance=account)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)

    def delete(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Account, pk=pk)
        if instance.id == self.request.user.account.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        flag = 0
        # for group in instance.groups.all():
        #     if group.access <= 2:
        #         flag += 1
        # if flag != 0:
        #     return Response(status=status.HTTP_403_FORBIDDEN)
        return self.destroy(self, request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.user.delete()


class AccountFirstPutView(GenericAPIView):
    serializer_class = AccountUpdateSerializer
    queryset = Account.objects.all().select_related('user', 'photo').prefetch_related('groups')
    authentication_classes = (AuthForAccountPut, )

    def put(self, request, pk=None, *args, **kwargs):
        account = get_object_or_404(Account, pk=pk)
        if account.id != request.user.account.id and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data, instance=account)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)


class RegisterStaffView(GenericAPIView):
    serializer_class = RegisterStaffSerializer
    queryset = User.objects.all()
    permission_classes = (IsAdmin,)

    def post(self, request, *args, **kwargs):
        request.data['host_domain'] = request.build_absolute_uri('/')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountListView(GenericAPIView, mixins.ListModelMixin):
    serializer_class = TestAccountSerializer    # TestAccountSerializer AccountSerializer
    queryset = Account.objects.all().select_related('user').prefetch_related('photo', 'groups').order_by('-user__is_active')
    permission_classes = (IsAdmin, )
    pagination_class = LimitStartPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'middle_name', 'user__phone_number', 'user__email',
                     'phone_number', 'email']

    @swagger_auto_schema(query_serializer=SwaggerAccountListParametr)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('start'):
            serializer = AccountListGetSerializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            if serializer.data.get('account_type') == 'kiosk':
                self.serializer_class = OfficePanelSerializer
                self.queryset = OfficePanelRelation.objects.all().select_related(
                    'floor', 'office', 'account','account__photo', 'account__user').prefetch_related('account__groups')
                return self.list(self, request, *args, **kwargs)
            if serializer.data.get('include_not_activated') == 'false':
                self.queryset = self.queryset.filter(user__is_active=True)
            if serializer.data.get('access_group'):
                self.queryset = self.queryset.filter(groups=serializer.data.get('access_group'))
            self.queryset.order_by('-user__is_active')
            return self.list(self, request, *args, **kwargs)
        elif request.query_params.get('access_group'):
            serializer = AccountListGetSerializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            if serializer.data.get('account_type') == 'kiosk':
                self.queryset = self.queryset.filter(account_type=serializer.data.get('account_type'))
            if serializer.data.get('include_not_activated') == 'false':
                self.queryset = self.queryset.filter(user__is_active=True)
            if serializer.data.get('access_group'):
                self.queryset = self.queryset.filter(groups=serializer.data.get('access_group'))
            return self.list(self, request, *args, **kwargs)
        else:
            self.pagination_class = None
            all_accounts = self.list(self, request, *args, **kwargs)
            response = dict()
            response['results'] = all_accounts.data
            return Response(response, status=status.HTTP_200_OK)


class ServiceEmailView(GenericAPIView):
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
        account_exist = get_object_or_404(Account, pk=request.data['account'])
        if not account_exist.email:
            return Response({'detail': 'Account has no email specified'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data['body'] and request.data['title']:
            send_mail(
                recipient_list=[account_exist.email],
                from_email=EMAIL_HOST_USER,
                subject=request.data['title'],
                message=''.join(request.data['body']),
            )
        return Response({'message': 'OK'}, status=status.HTTP_201_CREATED)


class UserAccessView(GenericAPIView):
    permission_classes = [IsAdmin, ]
    serializer_class = SwaggerAccountListParametr
    queryset = User.objects.all()

    def get(self, request, pk=None, *args, **kwargs):
        account = get_object_or_404(Account, pk=pk)
        if len(account.groups.all()) == 0:
            return Response([], status=status.HTTP_200_OK)
        else:
            response = []
            for group in account.groups.all():
                item = {
                    'id': group.id,
                    'title': group.title,
                    'offices': user_access_serializer(group.id)
                }
                response.append(item)
            return Response(response, status=status.HTTP_200_OK)


class OperatorPromotionView(GenericAPIView):
    permission_classes = [IsAdmin, ]

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'account': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        }
    ))
    def post(self, request, *args, **kwargs):
        account = get_object_or_404(Account, pk=request.data['account'])
        if not account.email:
            return Response({'detail': 'User has no email specified'}, status=status.HTTP_400_BAD_REQUEST)
        if not account.user.email:
            account.user.email = account.email
            account.user.is_staff = True
            password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()") for _ in range(8)])
            group = Group.objects.filter(access=2, is_deletable=False).first()
            account.user.set_password(password)
            account.user.save()
            account.groups.add(group)
            send_html_email_message(
                to=account.email,
                subject="Добро пожаловать в Simple-Office!",
                template_args={
                    'host': os.environ.get('ADMIN_HOST'),
                    'username': account.user.email,
                    'password': password
                }
            )
            return Response({'message': 'Promoted'}, status=status.HTTP_200_OK)
        else:
            account.user.password = None
            account.user.email = None
            account.user.is_staff = False
            account.user.save()
            for group in account.groups.all():
                if group.access == 2:
                    account.groups.remove(group)
            return Response({'message': 'Demoted'}, status=status.HTTP_200_OK)


class EnterCollectView(GenericAPIView):
    pass


# TODO: Add old token to blacklist
class PasswordChangeView(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = PasswordChangeSerializer

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


class PasswordResetView(GenericAPIView):
    serializer_class = PasswordResetSerializer

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


class EntranceCollectorView(GenericAPIView):
    serializer_class = EntranceCollectorSerializer
    authentication_classes = (AuthForAccountPut, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class RefreshTokenView(GenericAPIView):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({"detail": "Refresh parametr is required"}, status=400)
        refresh_ser = TokenRefreshSerializer(data=request.data)
        try:
            refresh_ser.is_valid(raise_exception=True)
        except TokenError as e:
            return Response(data={"detail": 'Refresh ' + ''.join(*e.args).lower()}, status=400)
        auth_dict = dict()
        auth_dict["refresh_token"] = str(refresh_ser.validated_data['refresh'])
        auth_dict["access_token"] = str(refresh_ser.validated_data['access'])
        return Response(auth_dict, status=200)


def custom404(request, exception=None):
    return JsonResponse({
        'status_code': 404,
        'message': 'Not found'
    }, status=404)


class OfficePanelRegister(GenericAPIView, mixins.CreateModelMixin):

    permission_classes = (IsAdmin, )
    serializer_class = OfficePanelSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class OfficePanelUpdate(GenericAPIView, mixins.UpdateModelMixin):

    queryset = Account.objects.all()
    permission_classes = (IsAdmin, )
    serializer_class = OfficePanelSerializer

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
