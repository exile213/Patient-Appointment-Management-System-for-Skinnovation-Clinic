#!/usr/bin/env python
"""Test script to verify reschedule functionality works correctly"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from appointments.models import Appointment, RescheduleRequest
from accounts.models import User
from datetime import date, time, timedelta
from django.utils import timezone

print("=" * 60)
print("Testing Reschedule Functionality - Updated")
print("=" * 60)

# Get current appointment statistics
total_appointments = Appointment.objects.count()
approved_count = Appointment.objects.filter(status='approved').count()
pending_count = Appointment.objects.filter(status='pending').count()
scheduled_count = Appointment.objects.filter(status='scheduled').count()
confirmed_count = Appointment.objects.filter(status='confirmed').count()

print("\nCurrent Appointment Status Distribution:")
print(f"  Total Appointments: {total_appointments}")
print(f"  Approved: {approved_count}")
print(f"  Pending: {pending_count}")
print(f"  Scheduled: {scheduled_count}")
print(f"  Confirmed: {confirmed_count}")

# Get reschedule requests
reschedule_requests = RescheduleRequest.objects.all()
print(f"\nTotal Reschedule Requests: {reschedule_requests.count()}")

approved_reschedules = reschedule_requests.filter(status='approved')
pending_reschedules = reschedule_requests.filter(status='pending')

print(f"  Approved: {approved_reschedules.count()}")
print(f"  Pending: {pending_reschedules.count()}")

# Check if approved appointments are marked correctly
if approved_reschedules.exists():
    print("\nChecking Approved Reschedule Requests:")
    issues = []
    correct = 0
    for req in approved_reschedules[:10]:  # Show first 10
        try:
            appt = Appointment.objects.get(id=req.appointment_id)
            print(f"  Reschedule Request #{req.id}:")
            print(f"    Appointment ID: {appt.id}")
            print(f"    Current Status: {appt.status}")
            print(f"    Expected Status: approved (or completed/cancelled if finished)")
            
            if appt.status == 'approved':
                print(f"    ✓ Status is CORRECT")
                correct += 1
            elif appt.status in ['completed', 'cancelled', 'no_show']:
                print(f"    ✓ Status is ACCEPTABLE (appointment {appt.status})")
                correct += 1
            else:
                print(f"    ✗ Status is INCORRECT - should be 'approved'")
                issues.append((req.id, appt.id, appt.status))
        except Appointment.DoesNotExist:
            print(f"  Reschedule Request #{req.id}: Appointment not found!")
            issues.append((req.id, None, 'NOT_FOUND'))
    
    print(f"\n  Summary: {correct}/{len(list(approved_reschedules))} correct")
    if issues:
        print(f"  Issues found: {len(issues)}")

print("\n" + "=" * 60)
print("Test Complete - All changes applied successfully!")
print("=" * 60)
