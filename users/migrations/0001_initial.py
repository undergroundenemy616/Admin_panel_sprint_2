# Generated by Django 3.0.8 on 2021-01-25 12:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import users.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('groups', '0001_initial'),
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('phone_number', models.CharField(blank=True, default=None, max_length=16, null=True, unique=True)),
                ('email', models.EmailField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('password', models.CharField(blank=True, max_length=512, null=True)),
                ('last_code', models.IntegerField(blank=True, default=users.models.activated_code, null=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', users.models.BookingUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('description', models.TextField(blank=True, default='', null=True)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(choices=[('male', 'male'), ('female', 'female'), ('undefined', 'undefined')], default='undefined', max_length=32)),
                ('first_name', models.CharField(blank=True, default='', max_length=64, null=True)),
                ('last_name', models.CharField(blank=True, default='', max_length=64, null=True)),
                ('middle_name', models.CharField(blank=True, default='', max_length=64, null=True)),
                ('city', models.IntegerField(default=None, null=True)),
                ('region_integer', models.IntegerField(blank=True, null=True)),
                ('district_integer', models.IntegerField(blank=True, null=True)),
                ('region_string', models.CharField(blank=True, default='', max_length=64, null=True)),
                ('district_string', models.CharField(blank=True, default='', max_length=64, null=True)),
                ('account_type', models.CharField(default='user', max_length=120)),
                ('email', models.EmailField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('phone_number', models.CharField(blank=True, default=None, max_length=16, null=True, unique=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(default=[], related_name='accounts', to='groups.Group')),
                ('photo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='files.File')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
