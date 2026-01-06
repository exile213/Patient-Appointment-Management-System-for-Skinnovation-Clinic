#!/usr/bin/env python
"""Script to check users in the database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from accounts.models import User
from django.db.models import Count

print(f'Total users: {User.objects.count()}')
print('\nUsers by type:')
for item in User.objects.values('user_type').annotate(count=Count('id')):
    print(f"  {item['user_type']}: {item['count']}")

print('\nDetailed user list:')
for user in User.objects.all().order_by('user_type', 'username'):
    print(f"  {user.username} ({user.user_type}) - Active: {user.is_active}")
