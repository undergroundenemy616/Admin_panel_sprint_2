# Generated by Django 3.0.8 on 2021-02-09 14:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='room',
            options={'ordering': ['floor__title']},
        ),
    ]
