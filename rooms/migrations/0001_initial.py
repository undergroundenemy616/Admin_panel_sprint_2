# Generated by Django 3.0.8 on 2020-11-09 14:32

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('files', '__first__'),
        ('room_types', '0001_initial'),
        ('floors', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=256)),
                ('description', models.CharField(blank=True, max_length=256, null=True)),
                ('seats_amount', models.IntegerField(default=1)),
                ('is_bookable', models.BooleanField(default=True)),
                ('floor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='floors.Floor')),
                ('images', models.ManyToManyField(blank=True, related_name='rooms', to='files.File')),
                ('type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rooms', to='room_types.RoomType')),
            ],
        ),
        migrations.CreateModel(
            name='RoomMarker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('icon', models.CharField(max_length=64)),
                ('x', models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(0)])),
                ('y', models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(0)])),
                ('room', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='room_marker', to='rooms.Room')),
            ],
        ),
    ]