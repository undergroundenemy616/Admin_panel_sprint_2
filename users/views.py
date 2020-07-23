from django.contrib.auth import user_logged_in
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
# from rest_framework.settings import api_settings
# from rest_framework_jwt.utils import jwt_encode_handler, jwt_get_secret_key
# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from users.models import User
from users.registration import register_or_send_sms, confirm_sms_code
from users.serializers import LoginOrRegisterSerializer


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
        elif sms_code and not created:
            result, msg = confirm_sms_code(sms_code, user.phone_number)
            user_logged_in.send(sender=user.__class__, user=user, request=request)
            # logic about creating token and forming user

        return

