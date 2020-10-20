from django.contrib.auth import user_logged_in, authenticate
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from users.backends import jwt_encode_handler, jwt_payload_handler
from users.models import User, Account
from users.registration import send_code, confirm_code
from users.serializers import (
    LoginOrRegisterSerializer,
    UserSerializer,
    AccountSerializer,
    LoginOrRegisterStaffSerializer
)


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

        try:
            data = {}
            if not sms_code:  # Register or login user
                send_code(user, created)
                data['status'], data['phone_number'] = 'DONE', user.phone_number
            elif sms_code and not created:  # Confirm code
                # Confirmation code
                confirm_code(phone_number, sms_code)
                user_logged_in.send(sender=user.__class__, user=user, request=request)

                # Create an account
                account = Account.objects.create(user_id=user.id)
                account.save()

                # Creating data for response
                data['auth'] = create_auth_data(user)
                data['status'], data['user'] = 'DONE', UserSerializer(instance=user).data
                data['account'] = AccountSerializer(instance=account).data
            else:
                raise ValueError('Invalid data!')
        except ValueError as error:
            data = {'message': str(error), 'status': 'ERROR'}
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
