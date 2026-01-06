from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Deactivate Jillian Ynares attendant account'

    def handle(self, *args, **options):
        # Deactivate User account
        user = User.objects.filter(
            first_name='Jillian',
            last_name='Ynares',
            user_type='attendant'
        ).first()
        
        if user:
            user.is_active = False
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deactivated User: {user.get_full_name()}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Jillian Ynares User account not found')
            )
        
        # Note: The user account is deactivated but kept for historical data
        # The account won't appear in active attendant lists
        
        self.stdout.write(
            self.style.SUCCESS('Jillian Ynares has been removed from active attendants')
        )
