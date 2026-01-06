from django.core.management.base import BaseCommand
from accounts.models import User
from django.contrib.auth import authenticate


class Command(BaseCommand):
    help = 'Check and fix attendant user account'

    def handle(self, *args, **options):
        username = 'attendant'
        password = 'attendant123'
        
        # Check if user exists
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'✓ User "{username}" exists in database')
            self.stdout.write(f'  - User Type: {user.user_type}')
            self.stdout.write(f'  - Is Active: {user.is_active}')
            self.stdout.write(f'  - Email: {user.email}')
            self.stdout.write(f'  - Full Name: {user.get_full_name()}')
            
            # Test authentication
            authenticated_user = authenticate(username=username, password=password)
            if authenticated_user:
                self.stdout.write(self.style.SUCCESS('✓ Authentication SUCCESSFUL'))
                self.stdout.write(f'  - Authenticated user type: {authenticated_user.user_type}')
                if authenticated_user.user_type != 'attendant':
                    self.stdout.write(self.style.WARNING(
                        f'⚠ WARNING: User type is "{authenticated_user.user_type}" but should be "attendant"'
                    ))
            else:
                self.stdout.write(self.style.ERROR('✗ Authentication FAILED'))
                self.stdout.write('  Attempting to reset password...')
                user.set_password(password)
                user.user_type = 'attendant'
                user.is_active = True
                user.save()
                self.stdout.write(self.style.SUCCESS('✓ Password reset and user type fixed'))
                
                # Test again
                authenticated_user = authenticate(username=username, password=password)
                if authenticated_user:
                    self.stdout.write(self.style.SUCCESS('✓ Authentication now SUCCESSFUL'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Authentication still FAILED'))
                    
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ User "{username}" does NOT exist'))
            self.stdout.write('Creating attendant user...')
            
            # Create the attendant user
            user = User.objects.create(
                username=username,
                email='attendant@beautyclinic.com',
                first_name='Clinic',
                last_name='Attendant',
                user_type='attendant',
                is_active=True
            )
            user.set_password(password)
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created user "{username}"'))
            self.stdout.write(f'  - Username: {username}')
            self.stdout.write(f'  - Password: {password}')
            self.stdout.write(f'  - User Type: {user.user_type}')
            
            # Test authentication
            authenticated_user = authenticate(username=username, password=password)
            if authenticated_user:
                self.stdout.write(self.style.SUCCESS('✓ Authentication SUCCESSFUL'))
            else:
                self.stdout.write(self.style.ERROR('✗ Authentication FAILED (this should not happen)'))

