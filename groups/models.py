import uuid
from django.core.exceptions import ValidationError
from django.db import models

ALLOWED_GROUPS = (
    ('client', 'client'),  # access 4
    # ('engineer', 'engineer'),  # access 3
    ('admin', 'admin'),  # access 2
    ('owner', 'owner'),  # access 1
    # ('superuser', 'superuser'),  # access 0
)

MAP_ACCESS = tuple((val, name[0]) for val, name in enumerate(reversed(ALLOWED_GROUPS)))
print(MAP_ACCESS)


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

    title = models.CharField(max_length=64, unique=True, default='client', null=False,
                             blank=False)
    access = models.IntegerField(validators=[integer_validator], default=4, null=False, blank=False)
    is_deletable = models.BooleanField(default=True, null=False, blank=False)

    def clean(self):
        # Custom groups (created by user) can be any.
        if (self.title, self.title) in ALLOWED_GROUPS and (self.access, self.title) not in MAP_ACCESS:
            msg = 'Access and title cannot be mapped!'
            raise ValidationError(msg)

    def delete(self, using=None, keep_parents=False):
        if not self.is_deletable:
            msg = f'This group {self.title} has non-deletable permissions.'
            raise ValidationError(msg)
        return super(Group, self).delete(using=None, keep_parents=False)
