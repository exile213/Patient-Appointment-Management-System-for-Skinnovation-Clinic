# Generated migration for TimeSlot model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0018_add_no_show_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.TimeField(help_text='Available appointment time slot', unique=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this time slot is available for booking')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Time Slot',
                'verbose_name_plural': 'Time Slots',
                'db_table': 'time_slots',
                'ordering': ['time'],
            },
        ),
    ]
