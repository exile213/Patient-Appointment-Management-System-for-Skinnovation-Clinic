from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date, time, timedelta
from faker import Faker
import random
import sys

from accounts.models import User
from services.models import Service
from products.models import Product, StockHistory
from packages.models import Package
from appointments.models import Appointment, Feedback, CancellationRequest, RescheduleRequest, Notification
from payments.models import Payment

User = get_user_model()
fake = Faker('en_PH')  # Filipino locale


class Command(BaseCommand):
    help = 'Seed database with 3 years of realistic patient data (2023-2025) using Faker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=200,
            help='Number of patients to create (default: 200)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing patient data before seeding'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview data generation without saving to database'
        )

    def handle(self, *args, **options):
        self.num_patients = options['patients']
        self.dry_run = options['dry_run']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            return
        
        # Clear existing data if requested
        if options['clear']:
            if not self.dry_run:
                self.clear_patient_data()
        
        try:
            with transaction.atomic():
                # Generate patients
                patients = self.create_patients()
                
                # Generate appointments with payments and feedback
                self.create_appointments_workflow(patients)
                
                # Generate analytics data
                if not self.dry_run:
                    self.populate_analytics()
                
                if self.dry_run:
                    self.stdout.write(self.style.WARNING('Dry run completed - rolling back transaction'))
                    raise Exception("Dry run - rolling back")
                
        except Exception as e:
            if not self.dry_run:
                self.stdout.write(self.style.ERROR(f'Error during seeding: {str(e)}'))
                raise
        
        if not self.dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully seeded {self.num_patients} patients with 3 years of data!'
                )
            )

    def validate_prerequisites(self):
        """Check if required data exists"""
        self.stdout.write('Validating prerequisites...')
        
        attendants = User.objects.filter(user_type='attendant')
        services = Service.objects.all()
        products = Product.objects.all()
        
        if not attendants.exists():
            self.stdout.write(self.style.ERROR('✗ No attendants found. Please create attendants first.'))
            return False
        
        if not services.exists():
            self.stdout.write(self.style.ERROR('✗ No services found. Please create services first.'))
            return False
        
        self.stdout.write(self.style.SUCCESS(f'✓ Found {attendants.count()} attendants'))
        self.stdout.write(self.style.SUCCESS(f'✓ Found {services.count()} services'))
        self.stdout.write(self.style.SUCCESS(f'✓ Found {products.count()} products'))
        
        return True

    def clear_patient_data(self):
        """Clear existing patient data while preserving admin/staff accounts"""
        self.stdout.write('Clearing existing patient data...')
        
        patient_users = User.objects.filter(user_type='patient')
        count = patient_users.count()
        
        if count > 0:
            # This will cascade delete appointments, feedback, payments, etc.
            patient_users.delete()
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {count} existing patients and related data'))
        else:
            self.stdout.write('No existing patient data found')

    def create_patients(self):
        """Generate realistic patients using Faker"""
        self.stdout.write(f'\nCreating {self.num_patients} patients...')
        
        patients = []
        existing_emails = set()
        existing_phones = set()
        
        # Get existing emails and phones to avoid duplicates
        if not self.dry_run:
            existing_emails = set(User.objects.values_list('email', flat=True))
            existing_phones = set(User.objects.values_list('phone', flat=True))
        
        for i in range(self.num_patients):
            # Generate unique email
            max_attempts = 10
            for attempt in range(max_attempts):
                first_name = fake.first_name()
                last_name = fake.last_name()
                email_base = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}"
                email = f"{email_base}@gmail.com"
                
                if email not in existing_emails:
                    existing_emails.add(email)
                    break
            else:
                # Fallback if we can't generate unique email
                email = f"patient{i}_{random.randint(1000, 9999)}@gmail.com"
                existing_emails.add(email)
            
            # Generate unique phone number (09XXXXXXXXX format)
            for attempt in range(max_attempts):
                phone = f"09{random.randint(100000000, 999999999)}"
                if phone not in existing_phones:
                    existing_phones.add(phone)
                    break
            
            # Generate username
            username = email.split('@')[0]
            
            # Random demographics
            gender = random.choices(
                ['female', 'male', 'other'],
                weights=[70, 28, 2],
                k=1
            )[0]
            
            civil_status = random.choices(
                ['single', 'married', 'divorced', 'widowed', 'separated'],
                weights=[60, 30, 5, 3, 2],
                k=1
            )[0]
            
            # Age between 18-65
            age = random.randint(18, 65)
            birthday = date.today() - timedelta(days=age * 365 + random.randint(0, 365))
            
            # Random middle name (50% have middle name)
            middle_name = fake.first_name() if random.random() > 0.5 else ''
            
            # Filipino address
            address = fake.address()
            
            # Occupation
            occupation = random.choice([
                'Student', 'Teacher', 'Nurse', 'Business Owner', 'Employee',
                'Entrepreneur', 'Government Employee', 'Sales Representative',
                'Manager', 'Professional', 'Homemaker', 'Freelancer'
            ])
            
            patient_data = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'middle_name': middle_name,
                'phone': phone,
                'gender': gender,
                'civil_status': civil_status,
                'birthday': birthday,
                'address': address,
                'occupation': occupation,
                'user_type': 'patient',
                'is_active': True,
            }
            
            if not self.dry_run:
                user = User.objects.create(**patient_data)
                user.set_password('patient123')
                user.save()
                patients.append(user)
            else:
                patients.append(patient_data)
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                self.stdout.write(f'  Created {i + 1}/{self.num_patients} patients...')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {self.num_patients} patients'))
        return patients

    def create_appointments_workflow(self, patients):
        """Create appointments for all patients across 3 years"""
        self.stdout.write('\nCreating appointments workflow...')
        
        # Date range: 2023-01-01 to 2025-12-31
        start_date = date(2023, 1, 1)
        end_date = date(2025, 12, 31)
        
        # Get available resources
        if not self.dry_run:
            attendants = list(User.objects.filter(user_type='attendant'))
            services = list(Service.objects.all())
            products = list(Product.objects.all())
            packages = list(Package.objects.all())
        else:
            attendants = ['attendant1', 'attendant2', 'attendant3']
            services = ['service1', 'service2']
            products = ['product1', 'product2']
            packages = ['package1']
        
        total_appointments = 0
        total_feedback = 0
        total_payments = 0
        
        # Patient visit patterns
        # 30% new (1-2 visits), 35% occasional (3-6), 25% regular (8-15), 10% loyal (20-40)
        visit_distribution = [
            (0.30, (1, 2)),    # New patients
            (0.35, (3, 6)),    # Occasional
            (0.25, (8, 15)),   # Regular
            (0.10, (20, 40)),  # Loyal
        ]
        
        for idx, patient in enumerate(patients):
            # Determine number of visits for this patient
            rand = random.random()
            cumulative = 0
            num_visits = 5  # default
            
            for probability, (min_visits, max_visits) in visit_distribution:
                cumulative += probability
                if rand <= cumulative:
                    num_visits = random.randint(min_visits, max_visits)
                    break
            
            # Generate appointments spread across 3 years
            appointment_dates = self.generate_appointment_dates(
                start_date, end_date, num_visits
            )
            
            for appt_date in appointment_dates:
                # Skip Sundays (clinic closed)
                if appt_date.weekday() == 6:  # Sunday
                    continue
                
                # Random time between 9 AM and 6 PM (15-min intervals)
                hour = random.randint(9, 17)
                minute = random.choice([0, 15, 30, 45])
                appt_time = time(hour, minute)
                
                # Random attendant
                attendant = random.choice(attendants)
                
                # Determine appointment type: 60% service, 25% product, 15% package
                appt_type = random.choices(
                    ['service', 'product', 'package'],
                    weights=[60, 25, 15],
                    k=1
                )[0]
                
                # Status distribution (relative to today's date)
                today = date.today()
                if appt_date < today:
                    # Past appointments
                    status = random.choices(
                        ['completed', 'cancelled', 'no_show'],
                        weights=[85, 10, 5],
                        k=1
                    )[0]
                elif appt_date == today:
                    status = random.choices(
                        ['confirmed', 'scheduled', 'completed'],
                        weights=[50, 30, 20],
                        k=1
                    )[0]
                else:
                    # Future appointments
                    status = random.choices(
                        ['scheduled', 'confirmed'],
                        weights=[60, 40],
                        k=1
                    )[0]
                
                # Create appointment based on type
                appointment_data = {
                    'patient': patient if not self.dry_run else patient['username'],
                    'attendant': attendant,
                    'appointment_date': appt_date,
                    'appointment_time': appt_time,
                    'status': status,
                }
                
                service_obj = None
                product_obj = None
                package_obj = None
                price = 0
                
                if appt_type == 'service' and services:
                    service_obj = random.choice(services)
                    appointment_data['service'] = service_obj
                    if not self.dry_run:
                        price = float(service_obj.price)
                    else:
                        price = 500.0
                        
                elif appt_type == 'product' and products:
                    product_obj = random.choice(products)
                    quantity = random.randint(1, 3)
                    appointment_data['product'] = product_obj
                    appointment_data['quantity'] = quantity
                    if not self.dry_run:
                        price = float(product_obj.price) * quantity
                    else:
                        price = 200.0 * quantity
                        
                elif appt_type == 'package' and packages:
                    package_obj = random.choice(packages)
                    appointment_data['package'] = package_obj
                    if not self.dry_run:
                        price = float(package_obj.price)
                    else:
                        price = 1500.0
                else:
                    # Fallback to service if chosen type not available
                    if services:
                        service_obj = random.choice(services)
                        appointment_data['service'] = service_obj
                        if not self.dry_run:
                            price = float(service_obj.price)
                        else:
                            price = 500.0
                
                # Create appointment
                if not self.dry_run:
                    appointment = Appointment.objects.create(**appointment_data)
                    total_appointments += 1
                    
                    # Create payment for completed/confirmed appointments
                    if status in ['completed', 'confirmed']:
                        payment_status = random.choices(
                            ['paid', 'partial', 'pending'],
                            weights=[95, 3, 2],
                            k=1
                        )[0]
                        
                        payment_method = random.choices(
                            ['cash', 'gcash', 'card', 'bank_transfer', 'other'],
                            weights=[50, 30, 15, 3, 2],
                            k=1
                        )[0]
                        
                        Payment.objects.create(
                            appointment=appointment,
                            amount=price,
                            amount_paid=price if payment_status == 'paid' else price * 0.5,
                            payment_status=payment_status,
                            payment_method=payment_method,
                            payment_date=timezone.now() if payment_status == 'paid' else None,
                        )
                        total_payments += 1
                    
                    # Create feedback for completed appointments (75-85% chance)
                    if status == 'completed' and random.random() < 0.80:
                        rating = random.choices(
                            [5, 4, 3, 2, 1],
                            weights=[50, 30, 15, 4, 1],
                            k=1
                        )[0]
                        
                        attendant_rating = random.choices(
                            [5, 4, 3, 2],
                            weights=[55, 30, 12, 3],
                            k=1
                        )[0]
                        
                        # Generate realistic comments
                        comments = self.generate_feedback_comment(rating)
                        
                        Feedback.objects.create(
                            appointment=appointment,
                            patient=patient,
                            rating=rating,
                            attendant_rating=attendant_rating,
                            comment=comments,
                        )
                        total_feedback += 1
                    
                    # Create stock history for product purchases
                    if product_obj and status == 'completed':
                        StockHistory.objects.create(
                            product=product_obj,
                            action='minus',
                            quantity=-quantity,
                            previous_stock=product_obj.stock,
                            new_stock=product_obj.stock - quantity,
                            reason=f'Purchased by {patient.get_full_name()} - Appointment #{appointment.id}',
                        )
                    
                    # Create cancellation/reschedule requests (5-8% of appointments)
                    if random.random() < 0.07:
                        if random.random() < 0.5:
                            # Cancellation request
                            CancellationRequest.objects.create(
                                appointment_id=appointment.id,
                                appointment_type='regular',
                                patient=patient,
                                reason=fake.sentence(),
                                status=random.choice(['pending', 'approved', 'rejected']),
                            )
                        else:
                            # Reschedule request
                            new_date = appt_date + timedelta(days=random.randint(1, 14))
                            RescheduleRequest.objects.create(
                                appointment_id=appointment.id,
                                patient=patient,
                                new_appointment_date=new_date,
                                new_appointment_time=appt_time,
                                reason=fake.sentence(),
                                status=random.choice(['pending', 'approved', 'rejected']),
                            )
                else:
                    total_appointments += 1
            
            # Progress indicator
            if (idx + 1) % 50 == 0:
                self.stdout.write(f'  Processed {idx + 1}/{len(patients)} patients...')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {total_appointments} appointments'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {total_payments} payments'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {total_feedback} feedback entries'))

    def generate_appointment_dates(self, start_date, end_date, num_visits):
        """Generate realistic appointment dates spread across date range"""
        dates = []
        total_days = (end_date - start_date).days
        
        if num_visits == 1:
            # Single visit - random date
            days_offset = random.randint(0, total_days)
            dates.append(start_date + timedelta(days=days_offset))
        else:
            # Multiple visits - spread them out
            # Divide the time period into segments
            segment_size = total_days // num_visits
            
            for i in range(num_visits):
                # Random date within this segment
                segment_start = i * segment_size
                segment_end = min((i + 1) * segment_size, total_days)
                days_offset = random.randint(segment_start, segment_end)
                dates.append(start_date + timedelta(days=days_offset))
        
        # Sort dates chronologically
        dates.sort()
        return dates

    def generate_feedback_comment(self, rating):
        """Generate realistic feedback comments based on rating"""
        if rating == 5:
            comments = [
                "Excellent service! Very professional and caring staff.",
                "Highly recommended! The treatment was amazing.",
                "Best beauty clinic in town! Will definitely come back.",
                "Very satisfied with the results. Thank you!",
                "Outstanding experience from start to finish.",
                "The staff made me feel very comfortable. Great service!",
                "Amazing results! Worth every peso.",
                "Professional and friendly attendants. Love it!",
            ]
        elif rating == 4:
            comments = [
                "Good service overall. Very satisfied.",
                "Great experience! Minor room for improvement.",
                "Professional staff and clean facility.",
                "Happy with the results. Will come back again.",
                "Good treatment, friendly staff.",
                "Satisfied with the service provided.",
                "Nice clinic with good service quality.",
            ]
        elif rating == 3:
            comments = [
                "Okay service. Could be better.",
                "Average experience. Nothing special.",
                "Decent service but a bit pricey.",
                "The service was fine, but took longer than expected.",
                "Fair service. Some improvements needed.",
                "It was okay. Expected more for the price.",
            ]
        elif rating == 2:
            comments = [
                "Service needs improvement.",
                "Not very satisfied with the experience.",
                "Expected better quality for the price.",
                "The wait time was too long.",
                "Disappointed with the service.",
            ]
        else:  # rating == 1
            comments = [
                "Very disappointed with the service.",
                "Poor experience. Would not recommend.",
                "Service did not meet expectations.",
                "Not satisfied at all.",
            ]
        
        return random.choice(comments)

    def populate_analytics(self):
        """Call the existing analytics population command"""
        self.stdout.write('\nPopulating analytics data...')
        
        try:
            from django.core.management import call_command
            call_command('populate_analytics', '--force')
            self.stdout.write(self.style.SUCCESS('✓ Analytics data populated'))
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Analytics population failed: {str(e)}')
            )
