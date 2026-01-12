from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('appointments', '0025_attendantunavailabilityrequest_pending_reassignment_choice_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Diagnosis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('diagnosis_date', models.DateField()),
                ('diagnosis_time', models.TimeField()),
                ('notes', models.TextField(blank=True, null=True, help_text='Clinical findings / diagnosis notes')),
                ('prescription', models.TextField(blank=True, null=True, help_text='Prescribed products or instructions')),
                ('follow_up_recommended', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='diagnosis', to='appointments.appointment')),
                ('diagnosed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diagnoses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'diagnoses',
                'ordering': ['-diagnosis_date', '-diagnosis_time'],
                'verbose_name': 'Diagnosis',
                'verbose_name_plural': 'Diagnoses',
            },
        ),
    ]
