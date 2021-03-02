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
from rest_framework import mixins, status
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from booking_api_django_new.settings import HARDCODED_PHONE_NUMBER, HARDCODED_SMS_CODE
from core.pagination import DefaultPagination, LimitStartPagination
from core.permissions import IsAdmin, IsAuthenticated, IsOwner
from groups.models import Group
from mail import send_html_email_message
from users.models import Account, User
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
                               EntranceCollectorSerializer, TestAccountSerializer)


class RegisterUserFromAdminPanelView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterUserFromAPSerializer
    permission_classes = (IsAdmin, )

    def post(self, request):
        if request.data.get('phone_number'):
            request.data['phone'] = request.data.get('phone_number')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.data.get('phone', None)
        user, created = User.objects.get_or_create(phone_number=phone_number)
        # Fix if we have user we dont need any actions

        account, account_created = Account.objects.get_or_create(user=user,
                                                                 description=serializer.data.get('description'))
        if account_created:
            user_group = Group.objects.get(access=4)
            account.groups.add(user_group)
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
        # if created:
        #     user.is_active = False
        #     user.save()
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
                    'new_code_in': 180,
                    'expires_in': 180,
                }
            elif sms_code:  # Confirm code  and user.is_active
                # first_login = True if user.last_login is None else False
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
            # elif not user.is_active:
            #     raise ValueError('User is not active')
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
    permission_classes = (IsAdmin,)

    def put(self, request, pk=None, *args, **kwargs):
        account = get_object_or_404(Account, pk=pk)
        serializer = self.serializer_class(data=request.data, instance=account)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)

    def delete(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Account, pk=pk)
        if instance.id == self.request.user.account.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        flag = 0
        for group in instance.groups.all():
            if group.access <= 2:
                flag += 1
        if flag != 0:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return self.destroy(self, request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.user.delete()


class RegisterStaffView(GenericAPIView):
    serializer_class = RegisterStaffSerializer
    queryset = User.objects.all()
    permission_classes = (IsOwner,)

    def post(self, request, *args, **kwargs):
        request.data['host_domain'] = request.build_absolute_uri('/')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountListView(GenericAPIView, mixins.ListModelMixin):
    serializer_class = TestAccountSerializer    # TestAccountSerializer AccountSerializer
    queryset = Account.objects.all().select_related('user').prefetch_related('photo', 'groups')
    permission_classes = (IsAdmin, )
    pagination_class = LimitStartPagination

    @swagger_auto_schema(query_serializer=SwaggerAccountListParametr)
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        if request.query_params.get('start'):
            if search:
                search = search.split(" ")
            if search and len(search) > 1:
                # Search by two words maybe: firstname and lastname
                self.queryset = Account.objects.filter(
                    Q(first_name__icontains=str(search[0]), last_name__icontains=str(search[1]))
                    | Q(first_name__icontains=str(search[1]), last_name__icontains=str(search[0]))
                ).select_related('user')
            elif search:
                # Search in firstname, lastname, middlename, phone_number, email
                self.queryset = Account.objects.filter(
                    Q(first_name__icontains=search[0])
                    | Q(last_name__icontains=search[0])
                    | Q(middle_name__icontains=search[0])
                    | Q(user__phone_number__icontains=search[0])
                    | Q(user__email__icontains=search[0])
                ).select_related('user')
            account_type = request.query_params.get('account_type')
            if account_type != 'user':
                # Added because of needs to handle kiosk account_type in future
                pass
            activated_flag = request.query_params.get('include_not_activated')
            if activated_flag == 'false':
                # Here we handle exclude of not activated accounts
                self.queryset = self.queryset.filter(user__is_active=True)
            return self.list(self, request, *args, **kwargs)
        elif search:
            search = search.split(" ")
            if len(search) > 1:
                # Search by two words maybe: firstname and lastname
                self.queryset = Account.objects.filter(
                    Q(first_name__icontains=str(search[0]), last_name__icontains=str(search[1]))
                    | Q(first_name__icontains=str(search[1]), last_name__icontains=str(search[0]))
                ).select_related('user')
            elif search:
                # Search in firstname, lastname, middlename, phone_number, email
                self.queryset = Account.objects.filter(
                    Q(first_name__icontains=search[0])
                    | Q(last_name__icontains=search[0])
                    | Q(middle_name__icontains=search[0])
                    | Q(user__phone_number__icontains=search[0])
                    | Q(user__email__icontains=search[0])
                ).select_related('user')
            account_type = request.query_params.get('account_type')
            if account_type != 'user':
                # Added because of needs to handle kiosk account_type in future
                pass
            activated_flag = request.query_params.get('include_not_activated')
            if activated_flag == 'false':
                # Here we handle exclude of not activated accounts
                self.queryset = self.queryset.filter(user__is_active=True)
            return self.list(self, request, *args, **kwargs)
        else:
            self.pagination_class = None
            all_accounts = self.list(self, request, *args, **kwargs)
            response = dict()
            # accounts = Account.objects.all()
            # result = []
            # for account in accounts:
            #     result.append(test_base_account_serializer(account))
            response['results'] = all_accounts.data
            # otvet = orjson.loads(orjson.dumps(response))
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
                subject="Добро пожаловать в Газпром!",
                template_args={
                    'host': request.build_absolute_uri('/'),
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
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class RefreshTokenView(GenericAPIView):

    def post(self, request, *args, **kwargs):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({"detail": "Refresh parametr is required."}, status=400)
        refresh_ser = TokenRefreshSerializer(data=request.data)
        refresh_ser.is_valid(raise_exception=True)
        access = refresh_ser.validated_data['access']
        payload = jwt.decode(jwt=access, verify=False)
        user = get_object_or_404(User, id=payload['user_id'])
        auth_dict = dict()
        token_serializer = TokenObtainPairSerializer()
        token = token_serializer.get_token(user=user)
        auth_dict["refresh_token"] = str(token)
        auth_dict["access_token"] = str(token.access_token)
        return Response(auth_dict, status=200)


def custom404(request, exception=None):
    return JsonResponse({
        'status_code': 404,
        'message': 'Not found'
    }, status=404)
