# Generated by Django 3.1.7 on 2021-08-06 11:56

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group_bookings', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupbooking',
            name='guests',
            field=models.JSONField(default=list, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
    ]