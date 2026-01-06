"""
Data migration script to fix existing approved reschedule requests.
Sets appointments with approved reschedule requests to 'approved' status.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from appointments.models import Appointment, RescheduleRequest

# Get all approved reschedule requests
approved_reschedules = RescheduleRequest.objects.filter(status='approved')

print(f"Found {approved_reschedules.count()} approved reschedule requests")

fixed_count = 0
errors = []

for req in approved_reschedules:
    try:
        appointment = Appointment.objects.get(id=req.appointment_id)
        
        # Only update if not already in a final state
        if appointment.status not in ['completed', 'cancelled', 'no_show']:
            old_status = appointment.status
            appointment.status = 'approved'
            appointment.save()
            fixed_count += 1
            print(f"✓ Updated Appointment #{appointment.id}: {old_status} → approved")
        else:
            print(f"  Skipped Appointment #{appointment.id}: Already in final state ({appointment.status})")
    except Appointment.DoesNotExist:
        errors.append(f"Appointment #{req.appointment_id} not found for reschedule request #{req.id}")

print(f"\n{'='*60}")
print(f"Migration Complete")
print(f"  Fixed: {fixed_count}")
print(f"  Errors: {len(errors)}")

if errors:
    print("\nErrors encountered:")
    for error in errors:
        print(f"  - {error}")
else:
    print("\nNo errors!")

print(f"{'='*60}")
