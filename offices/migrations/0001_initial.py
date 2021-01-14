# Generated by Django 3.0.8 on 2021-01-11 10:57

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('groups', '0001_initial'),
        ('files', '0001_initial'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Office',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=256)),
                ('description', models.CharField(blank=True, max_length=256, null=True)),
                ('working_hours', models.CharField(blank=True, max_length=128, null=True)),
                ('service_email', models.CharField(blank=True, max_length=256, null=True)),
                ('images', models.ManyToManyField(related_name='offices', to='files.File')),
                ('license', models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='office', to='licenses.License')),
            ],
        ),
        migrations.CreateModel(
            name='OfficeZone',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(default='Зона коворкинга', max_length=256)),
                ('is_deletable', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(related_name='groups', to='groups.Group')),
                ('office', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zones', to='offices.Office')),
            ],
        ),
    ]
