from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create Owner and Attendant users'

    def handle(self, *args, **options):
        # Create Owner user
        owner, created = User.objects.get_or_create(
            username='owner',
            defaults={
                'email': 'owner@beautyclinic.com',
                'first_name': 'Clinic',
                'last_name': 'Owner',
                'user_type': 'owner',
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            owner.set_password('owner123')
            owner.save()
            self.stdout.write(
                self.style.SUCCESS('Owner user created successfully!')
            )
        else:
            self.stdout.write('Owner user already exists.')

        # Create Attendant user
        attendant, created = User.objects.get_or_create(
            username='attendant',
            defaults={
                'email': 'attendant@beautyclinic.com',
                'first_name': 'Clinic',
                'last_name': 'Attendant',
                'user_type': 'attendant',
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            attendant.set_password('attendant123')
            attendant.save()
            self.stdout.write(
                self.style.SUCCESS('Attendant user created successfully!')
            )
        else:
            self.stdout.write('Attendant user already exists.')

        self.stdout.write('\nLogin credentials:')
        self.stdout.write('Owner: username=owner, password=owner123')
        self.stdout.write('Attendant: username=attendant, password=attendant123')
