# Generated by Django 3.0.8 on 2021-01-29 12:24

import uuid

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppEntrances',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entered_at', models.DateTimeField(auto_now=True)),
                ('ip_address', models.CharField(max_length=50, validators=[django.core.validators.validate_ipv46_address])),
                ('country', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('feed_view', models.BooleanField(default=False)),
                ('device_info', django.contrib.postgres.fields.jsonb.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entrance', to='users.Account')),
            ],
        ),
    ]
