# Generated by Django 3.0.8 on 2021-01-11 10:58

import datetime
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tables', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_from', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('date_to', models.DateTimeField()),
                ('date_activate_until', models.DateTimeField(null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_over', models.BooleanField(default=False)),
                ('theme', models.CharField(default='Без темы', max_length=200)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='existing_bookings', to='tables.Table')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Account')),
            ],
        ),
    ]
