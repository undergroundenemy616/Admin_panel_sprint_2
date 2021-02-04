# Generated by Django 3.0.8 on 2021-02-03 13:26

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TableMarker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x', models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(0)])),
                ('y', models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(0)])),
                ('table', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='table_marker', to='tables.Table')),
            ],
        ),
    ]
