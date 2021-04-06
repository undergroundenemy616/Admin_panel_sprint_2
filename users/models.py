import random
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import validate_ipv46_address
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from floors.models import Floor
from groups.models import Group
from offices.models import Office


def activated_code():
    """Returns random 4 integers."""
    return random.randint(1000, 9999)


class BookingUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, email, password, **extra_fields):
        """
        Create and save a user with the given phone, email, and password.
        """
        if phone_number is not None:
            phone_number = self.model.normalize_phone(phone_number=phone_number)
        if email is not None:
            email = self.normalize_email(email)
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        return self._create_user(phone_number, email, password, **extra_fields)

    def create_superuser(self, phone_number=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        return self._create_user(phone_number, email, password, **extra_fields)


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number: str = models.CharField(unique=True, default=None, max_length=16, null=True, blank=True)
    email = models.EmailField(unique=True, default=None, max_length=128, null=True, blank=True)
    password = models.CharField(max_length=512, blank=True, null=True)
    last_code = models.IntegerField(blank=True, null=True, default=activated_code)  # is this work?
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    objects = BookingUserManager()

    REQUIRED_FIELDS = []
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'id'

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

    def clean(self):
        try:
            self.normalize_phone(self.phone_number)
            self.check_pre_save()
        except ValueError as error:
            raise ValidationError(str(error))

    def check_pre_save(self):
        """Check admin user before saving"""
        if self.is_staff and not bool(self.email and self.password):
            raise ValueError('Employee must have `email` and `password` fields')
        elif not self.phone_number:
            raise ValueError('Client must have `phone_number` field')
        else:
            raise ValueError('Invalid data before saving.')

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

    # def delete(self, *args, **kwargs):
    #     self.is_deleted = True
    #     return super().delete(*args, **kwargs)


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    GENDERS = (
        ('male', 'male'),
        ('female', 'female'),
    )

    user = models.OneToOneField('User', on_delete=models.CASCADE)

    description = models.TextField(default='', blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(choices=GENDERS, max_length=32, default=None, null=True)
    first_name = models.CharField(default='', max_length=64, blank=True, null=True)
    last_name = models.CharField(default='', max_length=64, blank=True, null=True)
    middle_name = models.CharField(default='', max_length=64, blank=True, null=True)
    photo = models.ForeignKey('files.File', on_delete=models.SET_NULL, null=True)

    city = models.IntegerField(null=True, default=None)
    region_integer = models.IntegerField(null=True, blank=True)
    district_integer = models.IntegerField(null=True, blank=True)
    region_string = models.CharField(default='', max_length=64, blank=True, null=True)
    district_string = models.CharField(default='', max_length=64, blank=True, null=True)

    account_type = models.CharField(max_length=120, default='user')
    groups = models.ManyToManyField('groups.Group',
                                    default=[],
                                    related_name='accounts')
    email = models.EmailField(unique=True, default=None, max_length=128, null=True, blank=True)
    phone_number = models.CharField(unique=True, default=None, max_length=16, null=True, blank=True)

    updated_at = models.DateTimeField(null=False, auto_now=True)

    class Meta:
        ordering = ['user__created_at']
# Add validators


class AppEntrances(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entered_at = models.DateTimeField(auto_now=True)
    ip_address = models.CharField(max_length=50, validators=[validate_ipv46_address, ])
    country = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    feed_view = models.BooleanField(default=False)
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entrance')
    device_info = models.JSONField(encoder=DjangoJSONEncoder)


class OfficePanelRelation(models.Model):
    office = models.ForeignKey(Office, null=False, related_name='office_panels', on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, null=False, related_name='office_panels', on_delete=models.CASCADE)
    account = models.OneToOneField(Account, null=False, related_name='office_panels', on_delete=models.CASCADE)
    access_code = models.IntegerField(unique=True, null=False)


# class InfoPanel(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
#     title = models.CharField(max_length=64)
#     user = models.OneToOneField('User', on_delete=models.CASCADE)
#     office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=False, null=False)
#     floor = models.ForeignKey(Floor, on_delete=models.CASCADE, blank=False, null=False)

