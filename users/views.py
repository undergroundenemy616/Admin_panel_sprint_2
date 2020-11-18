import os

from django.contrib.auth import user_logged_in
from django.db.models import Q
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from core.pagination import DefaultPagination
from core.permissions import IsOwner, IsAdmin
from users.backends import jwt_encode_handler, jwt_payload_handler
from users.models import User, Account
from users.registration import send_code, confirm_code
from users.serializers import (
    LoginOrRegisterSerializer,
    AccountSerializer,
    LoginOrRegisterStaffSerializer, RegisterStaffSerializer, AccountUpdateSerializer, UserSerializer
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

        phone_number = serializer.data.get('phone_number', None)
        sms_code = serializer.data.pop('sms_code', None)
        user, created = User.objects.get_or_create(phone_number=phone_number)
        account, account_created = Account.objects.get_or_create(user=user,
                                                                 description=serializer.data.get('description'))
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
                data["user"] = UserSerializer(instance=user).data
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
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        account_id = request.query_params.get('id')
        if not account_id:
            user_id = request.user.id
            account_instance = get_object_or_404(Account, user=user_id)
        else:
            account_instance = get_object_or_404(Account, pk=account_id)
        serializer = self.serializer_class(instance=account_instance)
        return Response(serializer.to_representation(instance=account_instance), status=status.HTTP_200_OK)


class SingleAccountView(GenericAPIView):
    serializer_class = AccountUpdateSerializer
    queryset = Account.objects.all()
    permission_classes = (AllowAny, )

    def put(self, request, pk=None, *args, **kwargs):
        account = get_object_or_404(Account, pk=pk)
        serializer = self.serializer_class(data=request.data, instance=account)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.to_representation(instance=instance), status=status.HTTP_200_OK)


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
    permission_classes = (IsAdmin,)
    pagination_class = DefaultPagination

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
