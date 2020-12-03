# Generated by Django 3.0.8 on 2020-12-03 08:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0002_auto_20201130_0807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='height',
            field=models.IntegerField(default=0, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='file',
            name='size',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='width',
            field=models.IntegerField(default=0, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
