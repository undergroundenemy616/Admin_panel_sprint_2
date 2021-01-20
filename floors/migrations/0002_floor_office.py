# Generated by Django 3.0.8 on 2021-01-14 08:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('floors', '0001_initial'),
        ('offices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='floor',
            name='office',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='floors', to='offices.Office'),
        ),
    ]
