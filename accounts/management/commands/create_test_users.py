"""
Django management command to create all test users for Playwright tests
Run: python manage.py create_test_users
"""
from django.core.management.base import BaseCommand
from accounts.models import User
from django.contrib.auth import authenticate


class Command(BaseCommand):
    help = 'Create all test users for Playwright tests with correct credentials'

    def handle(self, *args, **options):
        test_users = [
            {
                'username': 'maria.santos',
                'password': 'TestPass123!',
                'user_type': 'patient',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'email': 'maria.santos@test.com',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'admin.staff',
                'password': 'AdminPass123!',
                'user_type': 'admin',
                'first_name': 'Admin',
                'last_name': 'Staff',
                'email': 'admin.staff@test.com',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'clinic.owner',
                'password': 'OwnerPass123!',
                'user_type': 'owner',
                'first_name': 'Clinic',
                'last_name': 'Owner',
                'email': 'clinic.owner@test.com',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'username': 'attendant.01',
                'password': 'AttendPass123!',
                'user_type': 'attendant',
                'first_name': 'Attendant',
                'last_name': 'One',
                'email': 'attendant.01@test.com',
                'is_staff': True,
                'is_superuser': False,
            },
        ]

        self.stdout.write('Creating test users for Playwright tests...\n')

        for user_data in test_users:
            username = user_data.pop('username')
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults=user_data
            )

            # Always update password and ensure user is active
            user.set_password(password)
            user.is_active = True
            user.user_type = user_data['user_type']
            user.is_staff = user_data['is_staff']
            user.is_superuser = user_data['is_superuser']
            user.save()

            status = 'created' if created else 'updated'
            self.stdout.write(
                self.style.SUCCESS(f'[OK] {username} ({user_data["user_type"]}) - {status}')
            )

            # Verify authentication
            auth_user = authenticate(username=username, password=password)
            if auth_user and auth_user.user_type == user_data['user_type']:
                self.stdout.write(
                    self.style.SUCCESS(f'  [OK] Authentication verified')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  [FAIL] Authentication FAILED')
                )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Test Users Summary:'))
        self.stdout.write('='*60)
        self.stdout.write('Patient:   maria.santos    / TestPass123!')
        self.stdout.write('Admin:     admin.staff     / AdminPass123!')
        self.stdout.write('Owner:     clinic.owner    / OwnerPass123!')
        self.stdout.write('Attendant: attendant.01   / AttendPass123!')
        self.stdout.write('='*60)

