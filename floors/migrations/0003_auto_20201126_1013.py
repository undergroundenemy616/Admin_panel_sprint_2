# Generated by Django 3.0.8 on 2020-11-26 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('floors', '0002_auto_20201116_1304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='floor',
            name='title',
            field=models.CharField(max_length=256),
        ),
    ]