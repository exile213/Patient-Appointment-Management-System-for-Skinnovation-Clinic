#!/usr/bin/env python
"""
Reset all user passwords in PostgreSQL database
This script resets passwords for all existing users to their documented passwords
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from accounts.models import User
from django.contrib.auth import authenticate

# Define all users and their passwords based on LOGIN_CREDENTIALS.md
user_passwords = {
    # Test users (from create_test_users command)
    'maria.santos': 'TestPass123!',
    'admin.staff': 'AdminPass123!',
    'clinic.owner': 'OwnerPass123!',
    'attendant.01': 'AttendPass123!',
    
    # Legacy users (from create_owner_attendant and create_superuser commands)
    'owner': 'owner123',
    'admin': 'admin123',
    'attendant': 'attendant123',
    
    # Additional attendants (common pattern)
    'Kikay': 'attendant123',
    'Mel': 'attendant123',
    'nilomarquez': 'attendant123',
    'patperez': 'attendant123',
    
    # Patient users (common pattern)
    'jeanurbano1803': 'patient123',
    'jrmurbano.chmsu': 'patient123',
    'kenai.reyes': 'patient123',
    'Kim': 'patient123',
    'ksreyes.chmsu': 'patient123',
    'Kurtzyy': 'patient123',
}

print("="*70)
print("  Password Reset for PostgreSQL Database")
print("="*70)
print()

success_count = 0
failed_count = 0
not_found_count = 0

for username, password in user_passwords.items():
    try:
        user = User.objects.get(username=username)
        
        # Reset password
        user.set_password(password)
        user.is_active = True  # Ensure user is active
        user.save()
        
        # Verify authentication
        auth_user = authenticate(username=username, password=password)
        if auth_user:
            print(f"✓ {username:20s} ({user.user_type:10s}) - Password reset successful")
            success_count += 1
        else:
            print(f"✗ {username:20s} ({user.user_type:10s}) - Password reset but auth failed")
            failed_count += 1
            
    except User.DoesNotExist:
        print(f"⚠ {username:20s} - User not found (skipping)")
        not_found_count += 1

print()
print("="*70)
print(f"  Summary:")
print(f"    ✓ Success: {success_count}")
print(f"    ✗ Failed:  {failed_count}")
print(f"    ⚠ Not Found: {not_found_count}")
print("="*70)
print()
print("Login Credentials Summary:")
print("-"*70)
print("Test Users (Recommended):")
print("  Patient:   maria.santos   / TestPass123!")
print("  Admin:     admin.staff    / AdminPass123!")
print("  Owner:     clinic.owner   / OwnerPass123!")
print("  Attendant: attendant.01   / AttendPass123!")
print()
print("Legacy Users:")
print("  Admin:     admin          / admin123")
print("  Owner:     owner          / owner123")
print("  Attendant: attendant      / attendant123")
print()
print("Other Attendants: (password: attendant123)")
print("  Kikay, Mel, nilomarquez, patperez")
print()
print("Other Patients: (password: patient123)")
print("  jeanurbano1803, jrmurbano.chmsu, kenai.reyes, Kim, ksreyes.chmsu, Kurtzyy")
print("="*70)
