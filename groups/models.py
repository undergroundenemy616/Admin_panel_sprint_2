import uuid

from django.core.exceptions import ValidationError
from django.db import models

ALLOWED_GROUPS = (
    ('guest', 'guest'),  # access 4
    ('employee', 'employee'),   # access 3
    ('admin', 'admin'),  # access 2
    ('owner', 'owner'),  # access 1
)

SUPERUSER_ACCESS = 0
OWNER_ACCESS = 1
ADMIN_ACCESS = 2
EMPLOYEE_ACCESS = 3
GUEST_ACCESS = 4


def integer_validator(value):
    min_val = 0
    max_val = 10
    if not isinstance(value, int):
        msg = 'Access must be an integer!'
        raise ValidationError(msg)
    if not min_val <= value <= max_val:
        msg = f'Access must be >= {min_val} and <= {max_val}!'
        raise ValidationError(msg)


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=64, unique=True, null=False, blank=False)
    description = models.CharField(max_length=64, null=True, blank=True)
    access = models.IntegerField(validators=[integer_validator], default=4, null=False, blank=False)
    is_deletable = models.BooleanField(default=True, null=False, blank=False)

    def clean(self):
        if (self.title, self.title) in ALLOWED_GROUPS \
                and self.access not in (OWNER_ACCESS, ADMIN_ACCESS, GUEST_ACCESS):
            msg = 'Access and title cannot be mapped!'
            raise ValidationError(msg)

    def delete(self, using=None, keep_parents=False):
        if not self.is_deletable:
            msg = f'This group {self.title} has non-deletable permissions.'
            raise ValidationError(msg)
        return super(Group, self).delete(using=None, keep_parents=False)

    @staticmethod
    def from_legacy_access(w: bool, m: bool, s: bool) -> int:
        if w:
            if m:
                if s:
                    return OWNER_ACCESS
                return ADMIN_ACCESS
            return EMPLOYEE_ACCESS
        return GUEST_ACCESS

    @staticmethod
    def to_legacy_access(access) -> dict:
        response = {}
        if access == OWNER_ACCESS:
            response['global_read'] = True
            response['global_write'] = True
            response['global_manage'] = True
            response['global_service'] = True
        elif access == ADMIN_ACCESS:
            response['global_read'] = True
            response['global_write'] = True
            response['global_manage'] = True
            response['global_service'] = False
        elif access in [GUEST_ACCESS, EMPLOYEE_ACCESS]:
            response['global_read'] = True
            response['global_write'] = False
            response['global_manage'] = False
            response['global_service'] = False
        return response

    class Meta:
        ordering = ['is_deletable', '-access']
