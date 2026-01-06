from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, Service
from products.models import Product
from packages.models import Package
from accounts.models import User, StoreHours

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        # Create service categories
        categories_data = [
            'Facials',
            'Anti-Aging & Face Lift',
            'Pico Laser',
            'Lightening Treatments',
            'Pimple Treatments',
            'Body Slimming with Cavitation',
            'Intense Pulsed Light (IPL) Hair Removal',
            'Other Services'
        ]
        
        for cat_name in categories_data:
            category, created = ServiceCategory.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(f'Created category: {cat_name}')

        # Create sample services
        services_data = [
            {
                'name': 'Primary Facial (Face)',
                'description': 'Basic facial treatment for the face',
                'price': 499.00,
                'duration': 60,
                'category': 'Facials'
            },
            {
                'name': 'Diamond Peel',
                'description': 'An exfoliating treatment to remove dead skin cells',
                'price': 499.00,
                'duration': 60,
                'category': 'Facials'
            },
            {
                'name': 'IPL Face',
                'description': 'Intense Pulsed Light treatment for hair removal on the face',
                'price': 499.00,
                'duration': 15,
                'category': 'Intense Pulsed Light (IPL) Hair Removal'
            },
            {
                'name': 'Underarm Whitening',
                'description': 'A treatment to lighten the skin in the underarm area',
                'price': 549.00,
                'duration': 15,
                'category': 'Lightening Treatments'
            }
        ]
        
        for service_data in services_data:
            category = ServiceCategory.objects.get(name=service_data['category'])
            service, created = Service.objects.get_or_create(
                service_name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'duration': service_data['duration'],
                    'category': category
                }
            )
            if created:
                self.stdout.write(f'Created service: {service_data["name"]}')

        # Create sample products
        products_data = [
            {
                'name': 'Derm Options Yellow Soap (Anti-Acne)',
                'description': 'Anti-Acne Soap',
                'price': 140.00,
                'stock': 100
            },
            {
                'name': 'Sunscreen Cream',
                'description': 'Apply to help skin fight UV rays',
                'price': 225.00,
                'stock': 100
            },
            {
                'name': 'Lightening Cream',
                'description': 'For night use',
                'price': 230.00,
                'stock': 100
            }
        ]
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                product_name=product_data['name'],
                defaults={
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'stock': product_data['stock']
                }
            )
            if created:
                self.stdout.write(f'Created product: {product_data["name"]}')

        # Create sample packages
        packages_data = [
            {
                'name': '3 + 1 Underarm Whitening',
                'description': 'Get 4 sessions for the price of 3',
                'price': 1847.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Diamond Peel',
                'description': 'Get 4 sessions for the price of 3',
                'price': 1697.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            }
        ]
        
        for package_data in packages_data:
            package, created = Package.objects.get_or_create(
                package_name=package_data['name'],
                defaults={
                    'description': package_data['description'],
                    'price': package_data['price'],
                    'sessions': package_data['sessions'],
                    'duration_days': package_data['duration_days'],
                    'grace_period_days': package_data['grace_period_days']
                }
            )
            if created:
                self.stdout.write(f'Created package: {package_data["name"]}')

        # Create sample attendants
        attendants_data = [
            {
                'first_name': 'Jillian',
                'last_name': 'Ynares',
                'shift_date': '2025-05-19',
                'shift_time': '10:00:00'
            },
            {
                'first_name': 'Nicole',
                'last_name': 'Pendon',
                'shift_date': '2025-05-19',
                'shift_time': '10:00:00'
            }
        ]
        
        for attendant_data in attendants_data:
            attendant, created = User.objects.get_or_create(
                user_type='attendant',
                first_name=attendant_data['first_name'],
                last_name=attendant_data['last_name'],
                defaults={
                    'username': f"attendant_{attendant_data['first_name'].lower()}_{attendant_data['last_name'].lower()}",
                    'email': f"{attendant_data['first_name'].lower()}.{attendant_data['last_name'].lower()}@example.com",
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created attendant: {attendant_data["first_name"]} {attendant_data["last_name"]}')

        # Create store hours
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days:
            store_hours, created = StoreHours.objects.get_or_create(
                day_of_week=day,
                defaults={
                    'open_time': '09:00:00',
                    'close_time': '17:00:00',
                    'is_closed': day == 'Sunday'
                }
            )
            if created:
                self.stdout.write(f'Created store hours for: {day}')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )
