from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Create a default attendant for appointments'

    def handle(self, *args, **options):
        # Create default attendant if it doesn't exist
        attendant, created = User.objects.get_or_create(
            id=1,
            user_type='attendant',
            defaults={
                'first_name': 'Admin',
                'last_name': 'Skinovation',
                'username': 'admin_skinnovation',
                'email': 'admin@skinovation.com',
                'phone': '0933 232 5122',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(f'Created default attendant: {attendant.first_name} {attendant.last_name}')
        else:
            self.stdout.write(f'Default attendant already exists: {attendant.first_name} {attendant.last_name}')

        self.stdout.write(
            self.style.SUCCESS('Default attendant setup complete')
        )
