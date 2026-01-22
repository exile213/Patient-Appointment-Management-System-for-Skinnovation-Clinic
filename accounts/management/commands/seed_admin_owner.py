from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default Admin and Owner users for the system'

    def handle(self, *args, **options):
        try:
            created_users = []
            
            # Create or reset default Owner
            # Check by email first, then by username
            owner = User.objects.filter(email='owner@skinovation.com').first()
            if not owner:
                # Check if username exists
                owner = User.objects.filter(username='owner').first()
            
            if not owner:
                # Create new user
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
                    self.style.SUCCESS('Owner user created successfully')
                )
            else:
                # Reset password and ensure account is active
                owner.set_password('owner@123456')
                owner.is_active = True
                owner.is_staff = True
                owner.user_type = 'owner'
                owner.first_name = 'Skinnovation'
                owner.last_name = 'Owner'
                owner.email = 'owner@skinovation.com'
                owner.phone = '09123456789'
                owner.username = 'owner'
                owner.save()
                created_users.append(('Owner', 'owner@skinovation.com', 'owner@123456'))
                self.stdout.write(
                    self.style.SUCCESS('Owner user password reset and account activated')
                )
            
            # Create or reset default Admin/Staff
            # Check by email first, then by username
            admin = User.objects.filter(email='admin@skinovation.com').first()
            if not admin:
                # Check if username exists
                admin = User.objects.filter(username='admin').first()
            
            if not admin:
                # Create new user
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
                    self.style.SUCCESS('Admin user created successfully')
                )
            else:
                # Reset password and ensure account is active
                admin.set_password('admin@123456')
                admin.is_active = True
                admin.is_staff = True
                admin.user_type = 'admin'
                admin.first_name = 'Admin'
                admin.last_name = 'Staff'
                admin.email = 'admin@skinovation.com'
                admin.phone = '09123456790'
                admin.username = 'admin'
                admin.save()
                created_users.append(('Admin', 'admin@skinovation.com', 'admin@123456'))
                self.stdout.write(
                    self.style.SUCCESS('Admin user password reset and account activated')
                )
            
            # Print credentials for all users
            if created_users:
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('USER CREDENTIALS'))
                self.stdout.write('='*60)
                for role, email, password in created_users:
                    self.stdout.write(f'\nRole: {role}')
                    self.stdout.write(f'Email: {email}')
                    self.stdout.write(f'Password: {password}')
                    if role == 'Owner':
                        self.stdout.write(f'Login URL: /accounts/login/owner/')
                    elif role == 'Admin':
                        self.stdout.write(f'Login URL: /accounts/login/admin/')
                self.stdout.write('='*60 + '\n')
            
            self.stdout.write(self.style.SUCCESS('\nAdmin and Owner seeding completed successfully!'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during seeding: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            sys.exit(1)
