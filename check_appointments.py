#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from appointments.models import Appointment
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
print(f'Today: {today}')
print(f'Total appointments: {Appointment.objects.count()}')
print(f'Last 30 days: {Appointment.objects.filter(appointment_date__gte=today - timedelta(days=30)).count()}')
print(f'Last 90 days: {Appointment.objects.filter(appointment_date__gte=today - timedelta(days=90)).count()}')
print(f'Last 365 days: {Appointment.objects.filter(appointment_date__gte=today - timedelta(days=365)).count()}')
print('\nAll appointment dates:')
for a in Appointment.objects.all().order_by('appointment_date'):
    print(f'  {a.id}: {a.appointment_date} - {a.status} - {a.patient.full_name}')
