# Generated by Django 3.0.8 on 2020-11-09 14:33

import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('issued_at', models.DateField(blank=True, null=True)),
                ('expires_at', models.DateField(blank=True, null=True)),
                ('support_available', models.BooleanField(default=False, null=True)),
                ('support_expires_at', models.DateField(blank=True, null=True)),
                ('tables_available', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('tables_infinite', models.BooleanField()),
                ('forever', models.BooleanField()),
            ],
        ),
    ]