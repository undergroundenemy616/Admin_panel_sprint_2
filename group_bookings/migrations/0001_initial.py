# Generated by Django 3.1.7 on 2021-07-26 12:08

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0012_auto_20210408_1424'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupBooking',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('guests', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_bookings', to='users.account')),
            ],
        ),
    ]
