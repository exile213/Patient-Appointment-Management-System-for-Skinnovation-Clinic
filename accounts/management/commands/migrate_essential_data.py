from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, Service
from products.models import Product
from packages.models import Package
from accounts.models import User
import mysql.connector
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate essential data from PHP MySQL database to Django'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='localhost', help='MySQL host')
        parser.add_argument('--user', default='root', help='MySQL username')
        parser.add_argument('--password', default='', help='MySQL password')
        parser.add_argument('--database', default='beauty_clinic2', help='MySQL database name')

    def handle(self, *args, **options):
        # Connect to MySQL database
        try:
            conn = mysql.connector.connect(
                host=options['host'],
                user=options['user'],
                password=options['password'],
                database=options['database']
            )
            cursor = conn.cursor(dictionary=True)
            self.stdout.write('Connected to MySQL database successfully!')
        except mysql.connector.Error as err:
            self.stdout.write(
                self.style.ERROR(f'Error connecting to MySQL: {err}')
            )
            return

        try:
            # Migrate Service Categories
            self.migrate_service_categories(cursor)
            
            # Migrate Services
            self.migrate_services(cursor)
            
            # Migrate Products
            self.migrate_products(cursor)
            
            # Migrate Packages
            self.migrate_packages(cursor)
            
            # Migrate Users (Patients, Admins, Owners)
            self.migrate_users(cursor)
            
            # Migrate Attendants (simplified)
            self.migrate_attendants_simple(cursor)

            self.stdout.write(
                self.style.SUCCESS('Essential data migration completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during migration: {e}')
            )
        finally:
            cursor.close()
            conn.close()

    def migrate_service_categories(self, cursor):
        self.stdout.write('Migrating service categories...')
        cursor.execute("SELECT * FROM service_categories")
        categories = cursor.fetchall()
        
        for cat in categories:
            category, created = ServiceCategory.objects.get_or_create(
                id=cat['category_id'],
                defaults={'name': cat['name']}
            )
            if created:
                self.stdout.write(f'  Created category: {cat["name"]}')

    def migrate_services(self, cursor):
        self.stdout.write('Migrating services...')
        cursor.execute("SELECT * FROM services")
        services = cursor.fetchall()
        
        for service in services:
            try:
                category = ServiceCategory.objects.get(id=service['category_id'])
                service_obj, created = Service.objects.get_or_create(
                    id=service['service_id'],
                    defaults={
                        'service_name': service['service_name'],
                        'description': service['description'] or '',
                        'price': float(service['price']) if service['price'] else 0.0,
                        'duration': service['duration'],
                        'category': category,
                        'image': service['image'] if service['image'] else None
                    }
                )
                if created:
                    self.stdout.write(f'  Created service: {service["service_name"]}')
            except ServiceCategory.DoesNotExist:
                self.stdout.write(f'  Skipped service {service["service_name"]} - category not found')

    def migrate_products(self, cursor):
        self.stdout.write('Migrating products...')
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        
        for product in products:
            product_obj, created = Product.objects.get_or_create(
                id=product['product_id'],
                defaults={
                    'product_name': product['product_name'],
                    'description': product['description'] or '',
                    'price': float(product['price']),
                    'stock': product['stock'],
                    'product_image': product['product_image'] if product['product_image'] else None
                }
            )
            if created:
                self.stdout.write(f'  Created product: {product["product_name"]}')

    def migrate_packages(self, cursor):
        self.stdout.write('Migrating packages...')
        cursor.execute("SELECT * FROM packages")
        packages = cursor.fetchall()
        
        for package in packages:
            package_obj, created = Package.objects.get_or_create(
                id=package['package_id'],
                defaults={
                    'package_name': package['package_name'],
                    'description': package['description'] or '',
                    'price': float(package['price']),
                    'sessions': package['sessions'],
                    'duration_days': package['duration_days'],
                    'grace_period_days': package['grace_period_days']
                }
            )
            if created:
                self.stdout.write(f'  Created package: {package["package_name"]}')

    def migrate_users(self, cursor):
        self.stdout.write('Migrating users...')
        
        # Migrate Patients
        cursor.execute("SELECT * FROM patients")
        patients = cursor.fetchall()
        
        for patient in patients:
            user, created = User.objects.get_or_create(
                id=patient['patient_id'],
                defaults={
                    'username': patient['username'],
                    'first_name': patient['first_name'],
                    'last_name': patient['last_name'],
                    'middle_name': patient['middle_name'] or '',
                    'phone': patient['phone'],
                    'user_type': 'patient',
                    'archived': bool(patient['archived'])
                }
            )
            if created:
                # Set password (you'll need to reset these)
                user.set_password('defaultpassword123')
                user.save()
                self.stdout.write(f'  Created patient: {patient["first_name"]} {patient["last_name"]}')

        # Migrate Admins
        cursor.execute("SELECT * FROM admin")
        admins = cursor.fetchall()
        
        for admin in admins:
            user, created = User.objects.get_or_create(
                id=admin['admin_id'],
                defaults={
                    'username': admin['admin_username'],
                    'first_name': admin['admin_first_name'],
                    'last_name': admin['admin_last_name'],
                    'user_type': 'admin',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                user.set_password('admin123')
                user.save()
                self.stdout.write(f'  Created admin: {admin["admin_first_name"]} {admin["admin_last_name"]}')

        # Migrate Owners
        cursor.execute("SELECT * FROM owners")
        owners = cursor.fetchall()
        
        for owner in owners:
            user, created = User.objects.get_or_create(
                id=owner['owner_id'],
                defaults={
                    'username': owner['username'],
                    'email': owner['email'],
                    'user_type': 'owner',
                    'is_staff': True
                }
            )
            if created:
                user.set_password('owner123')
                user.save()
                self.stdout.write(f'  Created owner: {owner["username"]}')

    def migrate_attendants_simple(self, cursor):
        self.stdout.write('Migrating attendants...')
        cursor.execute("SELECT * FROM attendants")
        attendants = cursor.fetchall()
        
        for attendant in attendants:
            # Convert timedelta to time string
            shift_time = attendant['shift_time']
            if hasattr(shift_time, 'total_seconds'):
                # It's a timedelta, convert to time
                total_seconds = int(shift_time.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                shift_time = f"{hours:02d}:{minutes:02d}:00"
            
            attendant_obj, created = User.objects.get_or_create(
                id=attendant['attendant_id'],
                user_type='attendant',
                defaults={
                    'first_name': attendant['first_name'],
                    'last_name': attendant['last_name'],
                    'username': f"attendant_{attendant['attendant_id']}",
                    'email': f"attendant_{attendant['attendant_id']}@example.com",
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  Created attendant: {attendant["first_name"]} {attendant["last_name"]}')
