# Generated by Django 3.0.8 on 2021-02-09 14:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ['is_deletable', '-access']},
        ),
    ]