#!/usr/bin/env python
"""
Simple script to seed Admin and Owner users without Django management command
Run this script when you need to create Owner and Admin users for the system.

Usage:
    python seed_users_simple.py

This script will:
1. Set up Django environment
2. Create or update Owner user
3. Create or update Admin user  
4. Display the credentials for login
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from accounts.models import User


def create_or_update_user(email, username, first_name, last_name, password, user_type, phone):
    """Create or update a user"""
    try:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'user_type': user_type,
                'phone': phone,
                'is_staff': True,
                'is_active': True,
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            return True, f"✓ {user_type.capitalize()} user created successfully"
        else:
            user.set_password(password)
            user.save()
            return True, f"✓ {user_type.capitalize()} user updated with new password"
    except Exception as e:
        return False, f"✗ Error creating {user_type} user: {str(e)}"


def main():
    """Main function to seed users"""
    print("\n" + "="*60)
    print("SKINNOVATION BEAUTY CLINIC - USER SEEDING")
    print("="*60 + "\n")
    
    try:
        created_users = []
        
        # Create Owner user
        success, message = create_or_update_user(
            email='owner@skinovation.com',
            username='owner',
            first_name='Skinnovation',
            last_name='Owner',
            password='owner@123456',
            user_type='owner',
            phone='09123456789'
        )
        print(message)
        if success:
            created_users.append({
                'role': 'Owner',
                'email': 'owner@skinovation.com',
                'password': 'owner@123456',
                'login_url': '/accounts/login/owner/'
            })
        
        # Create Admin user
        success, message = create_or_update_user(
            email='admin@skinovation.com',
            username='admin',
            first_name='Admin',
            last_name='Staff',
            password='admin@123456',
            user_type='admin',
            phone='09123456790'
        )
        print(message)
        if success:
            created_users.append({
                'role': 'Admin',
                'email': 'admin@skinovation.com',
                'password': 'admin@123456',
                'login_url': '/accounts/login/admin/'
            })
        
        # Display credentials
        if created_users:
            print("\n" + "="*60)
            print("LOGIN CREDENTIALS")
            print("="*60)
            for user_info in created_users:
                print(f"\n{user_info['role']} Account:")
                print(f"  Email:    {user_info['email']}")
                print(f"  Password: {user_info['password']}")
                print(f"  Login:    http://localhost:8000{user_info['login_url']}")
            print("\n" + "="*60 + "\n")
        
        print("✓ User seeding completed successfully!")
        print("\nNext steps:")
        print("1. Start the development server: python manage.py runserver")
        print("2. Visit the login page using the URL above")
        print("3. Log in with the credentials provided")
        print("4. Change the default passwords for security\n")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
