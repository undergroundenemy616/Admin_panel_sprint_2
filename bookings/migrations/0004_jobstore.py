# Generated by Django 3.1.7 on 2021-05-17 08:27

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_auto_20210225_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobStore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('job_id', models.CharField(max_length=100)),
                ('time_execute', models.DateTimeField()),
                ('parameters', models.JSONField()),
                ('executed', models.BooleanField(default=False)),
            ],
        ),
    ]
