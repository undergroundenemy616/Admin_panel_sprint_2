# Generated by Django 3.0.8 on 2021-01-11 10:57

import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=256)),
                ('path', models.CharField(max_length=256)),
                ('thumb', models.CharField(blank=True, max_length=256, null=True)),
                ('size', models.CharField(max_length=10, null=True)),
                ('width', models.IntegerField(default=0, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('height', models.IntegerField(default=0, null=True, validators=[django.core.validators.MinValueValidator(0)])),
            ],
        ),
    ]
