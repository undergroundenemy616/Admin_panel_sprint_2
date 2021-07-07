# Generated by Django 3.1.7 on 2021-07-06 13:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group_bookings', '0001_initial'),
        ('bookings', '0004_jobstore'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='group_booking',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='group_bookings.groupbooking'),
        ),
    ]
