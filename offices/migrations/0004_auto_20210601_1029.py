# Generated by Django 3.1.7 on 2021-06-01 10:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('offices', '0003_auto_20210209_1427'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='office',
            options={'ordering': ['-created_at']},
        ),
    ]