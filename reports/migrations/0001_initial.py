# Generated by Django 3.0.8 on 2021-01-25 12:17

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('offices', '0001_initial'),
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=120)),
                ('body', models.TextField()),
                ('id_delivered', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Account')),
                ('images', models.ManyToManyField(related_name='reports', to='files.File')),
                ('office', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offices.Office')),
            ],
        ),
    ]