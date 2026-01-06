#!/usr/bin/env python
"""Script to test password verification for users"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from accounts.models import User
from django.contrib.auth import authenticate

# Test users with correct passwords
test_cases = [
    ('owner', 'owner123'),
    ('clinic.owner', 'OwnerPass123!'),
    ('admin', 'admin123'),
    ('admin.staff', 'AdminPass123!'),
    ('attendant.01', 'AttendPass123!'),
    ('Kikay', 'attendant123'),
    ('jeanurbano1803', 'patient123'),
    ('maria.santos', 'TestPass123!'),
]

print("Testing authentication for common users:\n")
for username, password in test_cases:
    try:
        user = User.objects.get(username=username)
        print(f"User: {username} (Type: {user.user_type})")
        print(f"  - User exists: Yes")
        print(f"  - User is_active: {user.is_active}")
        print(f"  - Has usable password: {user.has_usable_password()}")
        
        # Test password check directly
        check_result = user.check_password(password)
        print(f"  - check_password('{password}'): {check_result}")
        
        # Test authenticate
        auth_user = authenticate(username=username, password=password)
        print(f"  - authenticate result: {auth_user is not None}")
        
        if not check_result:
            print(f"  - NOTE: Password '{password}' is incorrect for this user")
        print()
    except User.DoesNotExist:
        print(f"User: {username} - NOT FOUND\n")

print("\n" + "="*60)
print("Checking password hashes for a sample user:")
print("="*60)
owner = User.objects.filter(username='owner').first()
if owner:
    print(f"Owner password hash: {owner.password[:50]}...")
    print(f"Hash algorithm: {owner.password.split('$')[0] if '$' in owner.password else 'Unknown'}")
