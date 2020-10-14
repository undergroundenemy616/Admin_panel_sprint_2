# Generated by Django 3.0.8 on 2020-10-02 13:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import users.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('phone_number', models.CharField(max_length=16, unique=True)),
                ('username', models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ('email', models.EmailField(blank=True, max_length=128, null=True, unique=True)),
                ('password', models.CharField(blank=True, max_length=512, null=True)),
                ('last_code', models.IntegerField(blank=True, default=users.models.activated_code, null=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ForeignKey(default='e4f5cf2e-9ad2-4758-ad9d-26ee03c72c99', on_delete=django.db.models.deletion.CASCADE, related_name='users', to='groups.Group')),
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
                ('description', models.TextField(blank=True, default='')),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(choices=[('male', 'male'), ('female', 'female'), ('undefined', 'undefined')], default='undefined', max_length=32)),
                ('city', models.CharField(blank=True, default='', max_length=64)),
                ('first_name', models.CharField(blank=True, default='', max_length=64)),
                ('last_name', models.CharField(blank=True, default='', max_length=64)),
                ('middle_name', models.CharField(blank=True, default='', max_length=64)),
                ('region_integer', models.IntegerField(blank=True, null=True)),
                ('district_integer', models.IntegerField(blank=True, null=True)),
                ('region_string', models.CharField(blank=True, default='', max_length=64)),
                ('district_string', models.CharField(blank=True, default='', max_length=64)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
