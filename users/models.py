import random
import uuid
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin, Group
from django.core.exceptions import ValidationError
from django.db import models


class BookingUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, email, password, **extra_fields):
        """
        Create and save a user with the given phone, email, and password.
        """
        if not phone_number:
            raise ValueError('The given phone must be set')
        if email is not None:
            email = self.normalize_email(email)
        phone_number = self.model.normalize_phone(phone_number=phone_number)
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone_number, email, password, **extra_fields)

    def create_superuser(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone_number, email, password, **extra_fields)


def activated_code():
    """Returns random 4 integers"""
    return random.randint(1000, 9999)


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(unique=True, max_length=16)
    username = models.CharField(unique=True, max_length=64, null=True, blank=True)
    email = models.EmailField(unique=True, max_length=128, null=True, blank=True)
    password = models.CharField(max_length=512, blank=True, null=True)

    last_code = models.IntegerField(blank=True, null=True, default=activated_code)
    groups = models.ForeignKey('groups.Group', default=4, related_name='users', on_delete=models.CASCADE)

    is_staff = models.BooleanField(default=False)  # Mocked
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=False, auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(null=False, auto_now=True)

    objects = BookingUserManager()

    REQUIRED_FIELDS = []
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'phone_number'

    @classmethod
    def normalize_phone(cls, phone_number):
        if not cls.check_phone_len(phone_number):
            msg = 'Phone number must be greater or equal than 11 characters and less or equal than 16 for normalize it!'
            raise ValueError(msg)

        if phone_number.startswith('8') and len(phone_number) == 11 and phone_number.isdigit():
            return '+7' + phone_number[1:]
        elif phone_number.startswith('+7') and len(phone_number) == 12 and phone_number[1:].isdigit():
            return phone_number
        elif phone_number.startswith('+8') and len(phone_number) == 12 and phone_number[1:].isdigit():
            return '+7' + phone_number[2:]
        elif phone_number.startswith('+') and phone_number[1:].isdigit():
            return phone_number
        elif phone_number.isdigit():
            return '+' + phone_number
        else:
            msg = 'Phone number must contains only digits and plus character in begin.'
            raise ValueError(msg)

    @staticmethod
    def check_phone_len(phone_number):
        """Phone len must be 12 chars. If it is not, returns False"""
        return 11 <= len(phone_number) <= 16

    def clean(self):  # TODO
        try:
            self.normalize_phone(self.phone_number)
        except ValueError as error:
            raise ValidationError(str(error))

    def check_sms_code(self, sms_code):
        """Method compare inputted sms_code and user`s code.
        Do not use method for confirming and validating sms from client. For that we have Redis.cache!"""
        return self.last_code == sms_code

    def get_password(self):
        """Returns password if it exists."""
        return self.password or None

    def get_email(self):
        """Returns email if it exists."""
        return self.email or None


class Account(models.Model):
    GENDERS = (
        ('male', 'male'),
        ('female', 'female'),
        ('undefined', 'undefined')
    )

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts')

    # account_type = models.CharField(max_length=128, default)  # TODO

    description = models.TextField(default='', blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(choices=GENDERS, max_length=32, default='undefined')

    city = models.CharField(default='', max_length=64, blank=True)  # TODO

    first_name = models.CharField(default='', max_length=64, blank=True)  # TODO
    last_name = models.CharField(default='', max_length=64, blank=True)  # TODO
    middle_name = models.CharField(default='', max_length=64, blank=True)  # TODO

    region_integer = models.IntegerField(null=True, blank=True)  # TODO
    district_integer = models.IntegerField(null=True, blank=True)  # TODO

    region_string = models.CharField(default='', max_length=64, blank=True)  # TODO
    district_string = models.CharField(default='', max_length=64, blank=True)  # TODO

    photo = None  # todo

    updated_at = models.DateTimeField(null=False, auto_now=True)

# Add validators
