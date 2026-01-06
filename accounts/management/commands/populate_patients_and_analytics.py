from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from accounts.models import User
from services.models import Service
from products.models import Product
from packages.models import Package
from appointments.models import Appointment, Feedback
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample patients, appointments, and analytics data'

    def handle(self, *args, **options):
        # Create sample patients
        self.create_sample_patients()
        
        # Create sample appointments
        self.create_sample_appointments()
        
        # Populate analytics
        self.stdout.write('Running analytics population...')
        from django.core.management import call_command
        call_command('populate_analytics', '--force')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated patients, appointments, and analytics!')
        )

    def create_sample_patients(self):
        """Create sample patient users"""
        self.stdout.write('Creating sample patients...')
        
        patients_data = [
            {
                'username': 'maria.santos',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'email': 'maria.santos@example.com',
                'phone': '09123456789',
                'gender': 'female',
                'birthday': date(1990, 5, 15),
            },
            {
                'username': 'juan.dela.cruz',
                'first_name': 'Juan',
                'last_name': 'Dela Cruz',
                'email': 'juan.delacruz@example.com',
                'phone': '09123456790',
                'gender': 'male',
                'birthday': date(1988, 8, 20),
            },
            {
                'username': 'ana.reyes',
                'first_name': 'Ana',
                'last_name': 'Reyes',
                'email': 'ana.reyes@example.com',
                'phone': '09123456791',
                'gender': 'female',
                'birthday': date(1995, 3, 10),
            },
            {
                'username': 'carlos.garcia',
                'first_name': 'Carlos',
                'last_name': 'Garcia',
                'email': 'carlos.garcia@example.com',
                'phone': '09123456792',
                'gender': 'male',
                'birthday': date(1992, 11, 25),
            },
            {
                'username': 'sophia.lopez',
                'first_name': 'Sophia',
                'last_name': 'Lopez',
                'email': 'sophia.lopez@example.com',
                'phone': '09123456793',
                'gender': 'female',
                'birthday': date(1993, 7, 5),
            },
            {
                'username': 'miguel.torres',
                'first_name': 'Miguel',
                'last_name': 'Torres',
                'email': 'miguel.torres@example.com',
                'phone': '09123456794',
                'gender': 'male',
                'birthday': date(1989, 12, 18),
            },
            {
                'username': 'isabella.martinez',
                'first_name': 'Isabella',
                'last_name': 'Martinez',
                'email': 'isabella.martinez@example.com',
                'phone': '09123456795',
                'gender': 'female',
                'birthday': date(1994, 4, 30),
            },
            {
                'username': 'diego.fernandez',
                'first_name': 'Diego',
                'last_name': 'Fernandez',
                'email': 'diego.fernandez@example.com',
                'phone': '09123456796',
                'gender': 'male',
                'birthday': date(1991, 9, 12),
            },
            {
                'username': 'emma.rodriguez',
                'first_name': 'Emma',
                'last_name': 'Rodriguez',
                'email': 'emma.rodriguez@example.com',
                'phone': '09123456797',
                'gender': 'female',
                'birthday': date(1996, 2, 22),
            },
            {
                'username': 'alejandro.morales',
                'first_name': 'Alejandro',
                'last_name': 'Morales',
                'email': 'alejandro.morales@example.com',
                'phone': '09123456798',
                'gender': 'male',
                'birthday': date(1990, 6, 8),
            },
        ]
        
        for patient_data in patients_data:
            user, created = User.objects.get_or_create(
                username=patient_data['username'],
                defaults={
                    'user_type': 'patient',
                    'first_name': patient_data['first_name'],
                    'last_name': patient_data['last_name'],
                    'email': patient_data['email'],
                    'phone': patient_data['phone'],
                    'gender': patient_data['gender'],
                    'birthday': patient_data['birthday'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password('patient123')
                user.save()
                self.stdout.write(f'Created patient: {patient_data["first_name"]} {patient_data["last_name"]}')

    def create_sample_appointments(self):
        """Create sample appointments for patients"""
        self.stdout.write('Creating sample appointments...')
        
        patients = User.objects.filter(user_type='patient')
        attendants = User.objects.filter(user_type='attendant')
        services = Service.objects.all()
        products = Product.objects.all()
        packages = Package.objects.all()
        
        if not patients.exists():
            self.stdout.write(self.style.WARNING('No patients found. Please create patients first.'))
            return
        
        if not attendants.exists():
            self.stdout.write(self.style.WARNING('No attendants found. Please create attendants first.'))
            return
        
        if not services.exists():
            self.stdout.write(self.style.WARNING('No services found. Please create services first.'))
            return
        
        # Create appointments for the last 90 days
        today = timezone.now().date()
        appointment_count = 0
        
        for patient in patients:
            # Create 3-8 appointments per patient
            num_appointments = random.randint(3, 8)
            
            for i in range(num_appointments):
                # Random date within last 90 days
                days_ago = random.randint(0, 90)
                appointment_date = today - timedelta(days=days_ago)
                
                # Random time between 9 AM and 5 PM
                from datetime import time
                hour = random.randint(9, 16)
                minute = random.choice([0, 15, 30, 45])
                appointment_time = time(hour, minute)
                
                # Random attendant
                attendant = random.choice(attendants)
                
                # Random service/product/package (70% service, 20% product, 10% package)
                rand = random.random()
                
                if rand < 0.7 and services.exists():
                    # Service appointment
                    service = random.choice(services)
                    appointment = Appointment.objects.create(
                        patient=patient,
                        attendant=attendant,
                        service=service,
                        appointment_date=appointment_date,
                        appointment_time=appointment_time,
                        status=random.choice(['completed', 'completed', 'completed', 'cancelled', 'pending']),
                    )
                    appointment_count += 1
                    
                    # Create feedback for completed appointments
                    if appointment.status == 'completed' and random.random() > 0.3:
                        Feedback.objects.get_or_create(
                            appointment=appointment,
                            patient=patient,
                            defaults={
                                'rating': random.choice([4, 5, 5, 5, 4, 4, 3]),
                                'attendant_rating': random.choice([4, 5, 5, 5]),
                                'comment': random.choice([
                                    'Great service!',
                                    'Very satisfied with the treatment.',
                                    'Professional staff.',
                                    'Will come back again.',
                                    'Excellent experience.',
                                    'Highly recommended.',
                                ])
                            }
                        )
                
                elif rand < 0.9 and products.exists():
                    # Product appointment
                    product = random.choice(products)
                    appointment = Appointment.objects.create(
                        patient=patient,
                        attendant=attendant,
                        product=product,
                        appointment_date=appointment_date,
                        appointment_time=appointment_time,
                        status=random.choice(['completed', 'completed', 'completed', 'cancelled']),
                    )
                    appointment_count += 1
                
                elif packages.exists():
                    # Package appointment
                    package = random.choice(packages)
                    appointment = Appointment.objects.create(
                        patient=patient,
                        attendant=attendant,
                        package=package,
                        appointment_date=appointment_date,
                        appointment_time=appointment_time,
                        status=random.choice(['completed', 'completed', 'completed', 'cancelled']),
                    )
                    appointment_count += 1
        
        self.stdout.write(f'Created {appointment_count} sample appointments')

