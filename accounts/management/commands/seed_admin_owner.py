from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default Admin and Owner users for the system'

    def handle(self, *args, **options):
        try:
            created_users = []
            
            # Create default Owner
            if not User.objects.filter(email='owner@skinovation.com').exists():
                owner = User.objects.create_user(
                    username='owner',
                    email='owner@skinovation.com',
                    first_name='Skinnovation',
                    last_name='Owner',
                    password='owner@123456',
                    user_type='owner',
                    phone='09123456789',
                    is_staff=True,
                    is_active=True
                )
                created_users.append(('Owner', 'owner@skinovation.com', 'owner@123456'))
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Owner user created successfully')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('✓ Owner user already exists (owner@skinovation.com)')
                )
            
            # Create default Admin/Staff
            if not User.objects.filter(email='admin@skinovation.com').exists():
                admin = User.objects.create_user(
                    username='admin',
                    email='admin@skinovation.com',
                    first_name='Admin',
                    last_name='Staff',
                    password='admin@123456',
                    user_type='admin',
                    phone='09123456790',
                    is_staff=True,
                    is_active=True
                )
                created_users.append(('Admin', 'admin@skinovation.com', 'admin@123456'))
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Admin user created successfully')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('✓ Admin user already exists (admin@skinovation.com)')
                )
            
            # Print credentials for newly created users
            if created_users:
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('NEW USER CREDENTIALS'))
                self.stdout.write('='*60)
                for role, email, password in created_users:
                    self.stdout.write(f'\nRole: {role}')
                    self.stdout.write(f'Email: {email}')
                    self.stdout.write(f'Password: {password}')
                self.stdout.write('='*60 + '\n')
            
            self.stdout.write(self.style.SUCCESS('\n✓ Admin and Owner seeding completed successfully!'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error during seeding: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            sys.exit(1)
