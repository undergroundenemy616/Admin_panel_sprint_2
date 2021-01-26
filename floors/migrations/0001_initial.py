# Generated by Django 3.0.8 on 2021-01-25 12:17

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('offices', '0001_initial'),
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Floor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=256)),
                ('description', models.CharField(blank=True, max_length=1024, null=True)),
                ('office', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='floors', to='offices.Office')),
            ],
        ),
        migrations.CreateModel(
            name='FloorMap',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('height', models.CharField(max_length=12, null=True)),
                ('width', models.CharField(max_length=12, null=True)),
                ('floor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='floors.Floor')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='files.File')),
            ],
        ),
    ]
