# Generated by Django 3.0.8 on 2021-02-20 09:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0002_tablemarker'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='table',
            options={'ordering': ['title']},
        ),
    ]