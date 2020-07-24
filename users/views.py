from django.contrib.auth import user_logged_in
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from users.backends import jwt_encode_handler, jwt_payload_handler
from users.models import User
from users.registration import register_or_send_sms, confirm_sms_code
from users.serializers import LoginOrRegisterSerializer, UserSerializer


def create_auth(user):
    """Create full auth dict with token, prefix, expiration
    and etc by given user."""
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    data = {'prefix': api_settings.JWT_AUTH_HEADER_PREFIX, 'token': token}
    return data


class LoginOrRegister(mixins.ListModelMixin, GenericAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = LoginOrRegisterSerializer

    def post(self, request):
        """Initial login, login"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        phone_number = data.get('phone_number', None)
        sms_code = data.get('sms_code', None)
        user, created = self.queryset.objects.get_or_create(phone_number=phone_number, last_code=sms_code)

        if not sms_code:
            result, msg = register_or_send_sms(created, user)
            if result is False:
                Response(data={'result': result, 'message': msg, 'extra_data': None}, status=400)
            Response(data={'result': result, 'message': msg, 'extra_data': None}, status=201)
        elif sms_code and not created:

            result, msg = confirm_sms_code(sms_code, user.phone_number)
            user_logged_in.send(sender=user.__class__, user=user, request=request)

            unverified_data = {'result': result, 'message': msg, 'extra_data': None}  # TODO них*** не понятно
            if result is False:
                return Response(data=unverified_data, status=400)

            # TODO logic for creating account

            data = unverified_data.update({'user': UserSerializer(instance=user).data, 'auth': create_auth(user)})
            Response(data=data, status=200)

        return Response('Invalid data!', status=400)
