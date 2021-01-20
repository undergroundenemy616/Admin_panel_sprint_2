import os
import random

from django.conf.global_settings import EMAIL_HOST_USER
from django.core.mail import send_mail

from django.contrib.auth import user_logged_in
from django.db.models import Q
from drf_yasg import  openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from core.pagination import DefaultPagination
from core.permissions import IsOwner, IsAdmin, IsAuthenticated
from mail import send_html_email_message
from users.backends import jwt_encode_handler, jwt_payload_handler
from users.models import User, Account
from users.registration import send_code, confirm_code
from users.serializers import (
    LoginOrRegisterSerializer,
    AccountSerializer,
    LoginOrRegisterStaffSerializer, RegisterStaffSerializer, AccountUpdateSerializer, UserSerializer,
    SwaggerAccountParametr, SwaggerAccountListParametr
)
from groups.models import Group


def create_auth_data(user):
    """Creates and returns a full auth dict with `token`, `prefix`."""
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return {'refresh_token': api_settings.JWT_AUTH_HEADER_PREFIX, 'access_token': token}


class LoginOrRegisterUser(mixins.ListModelMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = LoginOrRegisterSerializer

    def post(self, request):
        """Register or login view"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.data.get('phone', None)
        sms_code = serializer.data.pop('code', None)
        user, created = User.objects.get_or_create(phone_number=phone_number)
        if serializer.data.get('description'):
            account, account_created = Account.objects.get_or_create(user=user,
                                                                     description=serializer.data.get('description'))
        else:
            account, account_created = Account.objects.get_or_create(user=user)

        if account_created:
            user_group = Group.objects.get(access=4)
            account.groups.add(user_group)

        try:
            data = {}
            if not sms_code:  # Register or login user
                if not os.getenv('SMS_MOCK_CONFIRM'):
                    send_code(user, created)
                else:
                    print('SMS service is off, any code is acceptable')
                data['status'], data['phone_number'] = 'DONE', user.phone_number
                # Creating data for response
                data = {
                    'message': "OK",
                    'new_code_in': 180,
                    'expires_in': 180,
                }
            elif sms_code and not created:  # Confirm code
                if not os.getenv('SMS_MOCK_CONFIRM'):
                    # Confirmation code
                    confirm_code(phone_number, sms_code)
                else:
                    print('SMS service is off, any code is acceptable')
                user_logged_in.send(sender=user.__class__, user=user, request=request)

                # Creating data for response
                auth_data = create_auth_data(user)
                # data["user"] = UserSerializer(instance=user).data
                data["access_token"] = auth_data.get('access_token')
                data["refresh_token"] = data["access_token"]
                data["account"] = account.id
                data["activated"] = True
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
        return None, 'Incorrect email'

    is_correct = user.check_password(fields.get('password'))
    if not is_correct:
        return None, 'Incorrect password'

    if not user.is_staff or not user.is_active:
        return None, 'User is not a staff or has been blocked.'

    return user, None


class LoginStaff(GenericAPIView):
    serializer_class = LoginOrRegisterStaffSerializer
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, message = authenticate_staff(request, **serializer.validated_data)
        if not user:
            return Response({'detail': message}, status=400)
        # data = dict()
        auth_dict = create_auth_data(user)
        # data['status'], data['user'] = 'DONE', UserSerializer(instance=user).data
        return Response(auth_dict, status=200)


class AccountView(GenericAPIView):
    serializer_class = AccountSerializer
    queryset = Account.objects.all()
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
    queryset = Account.objects.all()
    permission_classes = (IsAdmin,)

    def put(self, request, pk=None, *args, **kwargs):
        account = get_object_or_404(Account, pk=pk)
        serializer = self.serializer_class(data=request.data, instance=account)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)

    def delete(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(Account, pk=pk)
        if instance.id == request.user.account.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        flag = 0
        for group in instance.groups.all():
            if group.access <= 2:
                flag += 1
        if flag != 0:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return self.destroy(self, request, *args, **kwargs)


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
    serializer_class = AccountSerializer
    queryset = Account.objects.all()
    permission_classes = (IsAdmin, )
    pagination_class = DefaultPagination

    @swagger_auto_schema(query_serializer=SwaggerAccountListParametr)
    def get(self, request, *args, **kwargs):
        if request.query_params.get('start'):
            search = request.query_params.get('search')
            if search:
                search = search.split(" ")
            if search and len(search) > 1:
                # Search by two words maybe: firstname and lastname
                self.queryset = Account.objects.filter(
                    Q(first_name__icontains=str(search[0]), last_name__icontains=str(search[1]))
                    | Q(first_name__icontains=str(search[1]), last_name__icontains=str(search[0]))
                )
            elif search:
                # Search in firstname, lastname, middlename, phone_number, email
                self.queryset = Account.objects.filter(
                    Q(first_name__icontains=search[0])
                    | Q(last_name__icontains=search[0])
                    | Q(middle_name__icontains=search[0])
                    | Q(user__phone_number__icontains=search[0])
                    | Q(user__email__icontains=search[0])
                )
            else:
                # Get all account to response
                self.queryset = Account.objects.all()
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
            response['results'] = all_accounts.data
            return Response(data=response, status=status.HTTP_200_OK)


class ServiceEmailView(GenericAPIView):
    queryset = Account.objects.all()
    permission_classes = [IsAdmin, ]

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'account': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
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
                message='\n'.join(request.data['body']),
            )
        return Response({'message': 'OK'}, status=status.HTTP_201_CREATED)

# TODO FIX FIX FIX FIX
class UserAccessView(GenericAPIView):
    permission_classes = [IsAdmin, ]

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
                    'offices': group.title  # Need to fix
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


