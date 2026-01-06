"""
Django management command to create 4 default attendant accounts
Run: python manage.py create_default_attendants
"""
from django.core.management.base import BaseCommand
from accounts.models import User, AttendantProfile
from django.contrib.auth import authenticate


class Command(BaseCommand):
    help = 'Create 4 default attendant accounts (Attendant 1, Attendant 2, Attendant 3, Attendant 4)'

    def handle(self, *args, **options):
        attendants_data = [
            {
                'number': 1,
                'username': 'attendant1',
                'first_name': 'Attendant',
                'last_name': '1',
                'email': 'attendant1@skinovation.com',
            },
            {
                'number': 2,
                'username': 'attendant2',
                'first_name': 'Attendant',
                'last_name': '2',
                'email': 'attendant2@skinovation.com',
            },
            {
                'number': 3,
                'username': 'attendant3',
                'first_name': 'Attendant',
                'last_name': '3',
                'email': 'attendant3@skinovation.com',
            },
            {
                'number': 4,
                'username': 'attendant4',
                'first_name': 'Attendant',
                'last_name': '4',
                'email': 'attendant4@skinovation.com',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for att_data in attendants_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                username=att_data['username'],
                defaults={
                    'user_type': 'attendant',
                    'first_name': att_data['first_name'],
                    'last_name': att_data['last_name'],
                    'email': att_data['email'],
                    'is_active': True
                }
            )
            
            # Update name if user already exists but name is different
            if not created:
                if user.first_name != att_data['first_name'] or user.last_name != att_data['last_name']:
                    user.first_name = att_data['first_name']
                    user.last_name = att_data['last_name']
                    user.save()
                    updated_count += 1
            
            # Set password
            default_password = f'attendant{att_data["number"]}123'
            user.set_password(default_password)
            user.is_active = True
            user.user_type = 'attendant'
            user.save()
            
            # Create or get attendant profile
            profile, profile_created = AttendantProfile.objects.get_or_create(
                user=user,
                defaults={
                    'work_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                    'start_time': '10:00',
                    'end_time': '18:00',
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created Attendant {att_data["number"]} - {user.get_full_name()}'
                    )
                )
                self.stdout.write(f'   Username: {att_data["username"]}')
                self.stdout.write(f'   Password: {default_password}')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'→ Attendant {att_data["number"]} already exists - {user.get_full_name()}'
                    )
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Summary: {created_count} created, {updated_count} updated, {len(attendants_data)} total attendants'
            )
        )


