"""
Django management command to create test patient user for Playwright tests
Run: python manage.py create_test_patient
"""
from django.core.management.base import BaseCommand
from accounts.models import User
from django.contrib.auth import authenticate


class Command(BaseCommand):
    help = 'Create test patient user for Playwright tests'

    def handle(self, *args, **options):
        # Create or update patient user
        user, created = User.objects.get_or_create(
            username='patient',
            defaults={
                'user_type': 'patient',
                'first_name': 'Test',
                'last_name': 'Patient',
                'email': 'patient@test.com',
                'is_active': True
            }
        )

        # Set password
        user.set_password('defaultpassword123')
        user.is_active = True
        user.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS('Patient user created successfully!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Patient user already exists - password updated!')
            )

        self.stdout.write(f'   Username: patient')
        self.stdout.write(f'   Password: defaultpassword123')

        # Verify the user can authenticate
        auth_user = authenticate(username='patient', password='defaultpassword123')
        if auth_user:
            self.stdout.write(
                self.style.SUCCESS('Authentication test: SUCCESS')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Authentication test: FAILED')
            )

