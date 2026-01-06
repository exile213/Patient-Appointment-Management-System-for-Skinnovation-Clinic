#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from accounts.models import User

jillian = User.objects.filter(first_name='Jillian', last_name='Ynares', user_type='attendant')
print(f'Found {jillian.count()} Jillian Ynares')
for j in jillian:
    print(f'  - {j.username}: is_active={j.is_active}')

# If found and active, deactivate
if jillian.exists():
    for j in jillian:
        if j.is_active:
            j.is_active = False
            j.save()
            print(f'Deactivated {j.username}')
        else:
            print(f'{j.username} already inactive')
else:
    print('No Jillian Ynares found')
