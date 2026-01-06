"""
Simple script to create a default admin user.
Run this if you need to create/reset the admin account.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from accounts.models import User

# Delete existing admin user if it exists
User.objects.filter(username='admin').delete()

# Create new admin user
try:
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print("=" * 50)
    print("Admin user created successfully!")
    print("=" * 50)
    print("Username: admin")
    print("Password: admin123")
    print("=" * 50)
except Exception as e:
    print(f"Error creating admin user: {e}")
    print("You can create one manually using: python manage.py createsuperuser")



