from django.contrib.auth import user_logged_in
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from users.backends import jwt_encode_handler, jwt_payload_handler
from users.models import User, Account
from users.registration import send_code, confirm_code
from users.serializers import LoginOrRegisterSerializer, UserSerializer, AccountSerializer


def create_auth_data(user):
    """Creates and returns a full auth dict with `token`, `prefix`."""
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return {'prefix': api_settings.JWT_AUTH_HEADER_PREFIX, 'token': token}


class LoginOrRegisterUser(mixins.ListModelMixin, GenericAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
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


class LoginOrRegisterEmployee(GenericAPIView):
    pass
