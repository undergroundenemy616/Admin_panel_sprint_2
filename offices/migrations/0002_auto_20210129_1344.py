# Generated by Django 3.0.8 on 2021-01-29 13:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('offices', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='officezone',
            unique_together={('title', 'office')},
        ),
    ]
