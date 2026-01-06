from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, Service
from products.models import Product
from packages.models import Package, PackageBooking, PackageAppointment
from appointments.models import Appointment, Notification
from accounts.models import User, StoreHours, ClosedDates
import mysql.connector
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate data from PHP MySQL database to Django'

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
            
            # Migrate Attendants
            self.migrate_attendants(cursor)
            
            # Migrate Store Hours
            self.migrate_store_hours(cursor)
            
            # Migrate Closed Dates
            self.migrate_closed_dates(cursor)
            
            # Migrate Appointments
            self.migrate_appointments(cursor)
            
            # Migrate Package Bookings
            self.migrate_package_bookings(cursor)
            
            # Migrate Package Appointments
            self.migrate_package_appointments(cursor)
            
            # Migrate Notifications
            self.migrate_notifications(cursor)

            self.stdout.write(
                self.style.SUCCESS('Data migration completed successfully!')
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
                        'image': service['image'] if service['image'] else None,
                        'created_at': service['created_at'],
                        'updated_at': service['updated_at']
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
                    'product_image': product['product_image'] if product['product_image'] else None,
                    'created_at': product['created_at'],
                    'updated_at': product['updated_at']
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
                    'grace_period_days': package['grace_period_days'],
                    'created_at': package['created_at'],
                    'updated_at': package['updated_at']
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
                    'archived': bool(patient['archived']),
                    'date_joined': patient['created_at']
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

    def migrate_attendants(self, cursor):
        self.stdout.write('Migrating attendants...')
        cursor.execute("SELECT * FROM attendants")
        attendants = cursor.fetchall()
        
        for attendant in attendants:
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

    def migrate_store_hours(self, cursor):
        self.stdout.write('Migrating store hours...')
        cursor.execute("SELECT * FROM store_hours")
        store_hours = cursor.fetchall()
        
        for hours in store_hours:
            hours_obj, created = StoreHours.objects.get_or_create(
                id=hours['id'],
                defaults={
                    'day_of_week': hours['day_of_week'],
                    'open_time': hours['open_time'],
                    'close_time': hours['close_time'],
                    'is_closed': bool(hours['is_closed'])
                }
            )
            if created:
                self.stdout.write(f'  Created store hours for: {hours["day_of_week"]}')

    def migrate_closed_dates(self, cursor):
        self.stdout.write('Migrating closed dates...')
        cursor.execute("SELECT * FROM closed_dates")
        closed_dates = cursor.fetchall()
        
        for date in closed_dates:
            date_obj, created = ClosedDates.objects.get_or_create(
                id=date['id'],
                defaults={
                    'start_date': date['start_date'],
                    'end_date': date['end_date'],
                    'reason': date['reason'] or ''
                }
            )
            if created:
                self.stdout.write(f'  Created closed date: {date["start_date"]} to {date["end_date"]}')

    def migrate_appointments(self, cursor):
        self.stdout.write('Migrating appointments...')
        cursor.execute("SELECT * FROM appointments")
        appointments = cursor.fetchall()
        
        for appointment in appointments:
            try:
                patient = User.objects.get(id=appointment['patient_id'])
                attendant = User.objects.get(id=appointment['attendant_id'], user_type='attendant')
                
                service = None
                product = None
                package = None
                
                if appointment['service_id']:
                    service = Service.objects.get(id=appointment['service_id'])
                if appointment['product_id']:
                    product = Product.objects.get(id=appointment['product_id'])
                if appointment['package_id']:
                    package = Package.objects.get(id=appointment['package_id'])
                
                appointment_obj, created = Appointment.objects.get_or_create(
                    id=appointment['appointment_id'],
                    defaults={
                        'patient': patient,
                        'service': service,
                        'product': product,
                        'package': package,
                        'attendant': attendant,
                        'appointment_date': appointment['appointment_date'],
                        'appointment_time': appointment['appointment_time'],
                        'status': appointment['status'],
                        'created_at': appointment['created_at'],
                        'updated_at': appointment['updated_at']
                    }
                )
                if created:
                    self.stdout.write(f'  Created appointment for: {patient.first_name} {patient.last_name}')
            except (User.DoesNotExist, Service.DoesNotExist, Product.DoesNotExist, Package.DoesNotExist) as e:
                self.stdout.write(f'  Skipped appointment {appointment["appointment_id"]} - {e}')

    def migrate_package_bookings(self, cursor):
        self.stdout.write('Migrating package bookings...')
        cursor.execute("SELECT * FROM package_bookings")
        bookings = cursor.fetchall()
        
        for booking in bookings:
            try:
                patient = User.objects.get(id=booking['patient_id'])
                package = Package.objects.get(id=booking['package_id'])
                
                booking_obj, created = PackageBooking.objects.get_or_create(
                    id=booking['booking_id'],
                    defaults={
                        'patient': patient,
                        'package': package,
                        'sessions_remaining': booking['sessions_remaining'],
                        'valid_until': booking['valid_until'],
                        'grace_period_until': booking['grace_period_until'],
                        'created_at': booking['created_at'],
                        'updated_at': booking['updated_at']
                    }
                )
                if created:
                    self.stdout.write(f'  Created package booking for: {patient.first_name} {patient.last_name}')
            except (User.DoesNotExist, Package.DoesNotExist) as e:
                self.stdout.write(f'  Skipped package booking {booking["booking_id"]} - {e}')

    def migrate_package_appointments(self, cursor):
        self.stdout.write('Migrating package appointments...')
        cursor.execute("SELECT * FROM package_appointments")
        appointments = cursor.fetchall()
        
        for appointment in appointments:
            try:
                booking = PackageBooking.objects.get(id=appointment['booking_id'])
                attendant = User.objects.get(id=appointment['attendant_id'], user_type='attendant')
                
                appointment_obj, created = PackageAppointment.objects.get_or_create(
                    id=appointment['package_appointment_id'],
                    defaults={
                        'booking': booking,
                        'attendant': attendant,
                        'appointment_date': appointment['appointment_date'],
                        'appointment_time': appointment['appointment_time'],
                        'status': appointment['status'],
                        'created_at': appointment['created_at'],
                        'updated_at': appointment['updated_at']
                    }
                )
                if created:
                    self.stdout.write(f'  Created package appointment for: {booking.patient.first_name} {booking.patient.last_name}')
            except (PackageBooking.DoesNotExist, User.DoesNotExist) as e:
                self.stdout.write(f'  Skipped package appointment {appointment["package_appointment_id"]} - {e}')

    def migrate_notifications(self, cursor):
        self.stdout.write('Migrating notifications...')
        cursor.execute("SELECT * FROM notifications")
        notifications = cursor.fetchall()
        
        for notification in notifications:
            patient = None
            if notification['patient_id']:
                try:
                    patient = User.objects.get(id=notification['patient_id'])
                except User.DoesNotExist:
                    pass
            
            notification_obj, created = Notification.objects.get_or_create(
                id=notification['notification_id'],
                defaults={
                    'type': notification['type'],
                    'appointment_id': notification['appointment_id'],
                    'title': notification['title'],
                    'message': notification['message'],
                    'patient': patient,
                    'is_read': bool(notification['is_read']),
                    'created_at': notification['created_at']
                }
            )
            if created:
                self.stdout.write(f'  Created notification: {notification["title"]}')
