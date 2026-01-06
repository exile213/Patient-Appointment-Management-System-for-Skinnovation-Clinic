from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, Service
from products.models import Product
from packages.models import Package
from accounts.models import User, StoreHours

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with complete data including all services, products, and packages'

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
        
        category_map = {}
        for cat_name in categories_data:
            category, created = ServiceCategory.objects.get_or_create(name=cat_name)
            category_map[cat_name] = category
            if created:
                self.stdout.write(f'Created category: {cat_name}')

        # Create comprehensive services list based on templates
        services_data = [
            # Facials
            {'name': 'Primary Facial (Face)', 'description': 'A comprehensive facial treatment for the face area', 'price': 499.00, 'duration': 60, 'category': 'Facials'},
            {'name': 'Chest/Back', 'description': 'A facial treatment specifically for the chest or back area', 'price': 649.00, 'duration': 60, 'category': 'Facials'},
            {'name': 'Neck', 'description': 'A facial treatment targeting the neck area', 'price': 449.00, 'duration': 60, 'category': 'Facials'},
            {'name': 'Charcoal', 'description': 'A facial that includes a Diamond Peel and a Charcoal mask for deep cleansing and purification', 'price': 699.00, 'duration': 60, 'category': 'Facials'},
            {'name': 'Diamond Peel', 'description': 'Exfoliating facial treatment using diamond-tipped wand', 'price': 599.00, 'duration': 60, 'category': 'Facials'},
            {'name': 'Snow White', 'description': 'Brightening facial treatment', 'price': 699.00, 'duration': 60, 'category': 'Facials'},
            {'name': 'Casmara', 'description': 'Premium facial mask treatment', 'price': 799.00, 'duration': 90, 'category': 'Facials'},
            
            # Anti-Aging & Face Lift
            {'name': 'Collagen', 'description': 'Anti-aging facial treatment with collagen infusion', 'price': 799.00, 'duration': 90, 'category': 'Anti-Aging & Face Lift'},
            {'name': 'Oxygeneo', 'description': '3-in-1 facial treatment that exfoliates, infuses, and oxygenates', 'price': 899.00, 'duration': 90, 'category': 'Anti-Aging & Face Lift'},
            {'name': 'Galvanic Therapy', 'description': 'Deep cleansing and anti-aging treatment using galvanic current', 'price': 699.00, 'duration': 60, 'category': 'Anti-Aging & Face Lift'},
            {'name': 'Geneo Infusion', 'description': 'Advanced facial treatment with infusion technology', 'price': 999.00, 'duration': 90, 'category': 'Anti-Aging & Face Lift'},
            {'name': 'Platelet-Rich Plasma (PRP) therapy', 'description': 'Regenerative therapy using your own platelets', 'price': 2999.00, 'duration': 120, 'category': 'Anti-Aging & Face Lift'},
            {'name': 'Radio Frequency', 'description': 'Non-invasive skin tightening treatment', 'price': 1299.00, 'duration': 60, 'category': 'Anti-Aging & Face Lift'},
            
            # Pico Laser
            {'name': 'Pico Glow', 'description': 'Pico laser treatment for skin brightening', 'price': 1999.00, 'duration': 60, 'category': 'Pico Laser'},
            {'name': 'Tattoo Removal', 'description': 'Pico laser tattoo removal treatment', 'price': 2499.00, 'duration': 45, 'category': 'Pico Laser'},
            
            # Lightening Treatments
            {'name': 'Underarm Whitening', 'description': 'Skin lightening treatment for underarms', 'price': 599.00, 'duration': 45, 'category': 'Lightening Treatments'},
            {'name': 'Back Whitening', 'description': 'Skin lightening treatment for back area', 'price': 799.00, 'duration': 60, 'category': 'Lightening Treatments'},
            {'name': 'Butt Whitening', 'description': 'Skin lightening treatment for buttocks area', 'price': 899.00, 'duration': 60, 'category': 'Lightening Treatments'},
            {'name': 'Chest Whitening', 'description': 'Skin lightening treatment for chest area', 'price': 699.00, 'duration': 60, 'category': 'Lightening Treatments'},
            {'name': 'Neck Whitening', 'description': 'Skin lightening treatment for neck area', 'price': 599.00, 'duration': 45, 'category': 'Lightening Treatments'},
            {'name': 'Skin Rejuvenation', 'description': 'Comprehensive skin rejuvenation treatment', 'price': 1299.00, 'duration': 90, 'category': 'Lightening Treatments'},
            {'name': 'Vitamin C Infusion', 'description': 'Brightening treatment with Vitamin C', 'price': 899.00, 'duration': 60, 'category': 'Lightening Treatments'},
            
            # Pimple Treatments
            {'name': 'Anti-Acne Treatment', 'description': 'Specialized treatment for acne-prone skin', 'price': 699.00, 'duration': 60, 'category': 'Pimple Treatments'},
            
            # Body Slimming with Cavitation
            {'name': 'Arms Cavitation', 'description': 'Non-invasive body contouring for arms', 'price': 899.00, 'duration': 60, 'category': 'Body Slimming with Cavitation'},
            {'name': 'Waist Cavitation', 'description': 'Non-invasive body contouring for waist area', 'price': 999.00, 'duration': 60, 'category': 'Body Slimming with Cavitation'},
            {'name': 'Face Cavitation', 'description': 'Non-invasive facial contouring treatment', 'price': 799.00, 'duration': 45, 'category': 'Body Slimming with Cavitation'},
            
            # Intense Pulsed Light (IPL) Hair Removal
            {'name': 'IPL Face', 'description': 'Intense Pulsed Light treatment for facial hair removal', 'price': 899.00, 'duration': 45, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            {'name': 'IPL Underarms', 'description': 'IPL treatment for underarm hair removal', 'price': 499.00, 'duration': 30, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            {'name': 'IPL Legs', 'description': 'IPL treatment for leg hair removal', 'price': 1299.00, 'duration': 60, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            {'name': 'IPL Back', 'description': 'IPL treatment for back hair removal', 'price': 1199.00, 'duration': 60, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            {'name': 'IPL Bikini', 'description': 'IPL treatment for bikini area hair removal', 'price': 999.00, 'duration': 45, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            {'name': 'IPL Brazilian', 'description': 'IPL treatment for Brazilian area hair removal', 'price': 1299.00, 'duration': 45, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            {'name': 'IPL Upperlip', 'description': 'IPL treatment for upper lip hair removal', 'price': 399.00, 'duration': 15, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            
            # Other Services
            {'name': 'Carbon Doll Laser', 'description': 'Carbon laser treatment for deep pore cleansing', 'price': 799.00, 'duration': 45, 'category': 'Other Services'},
            {'name': 'Warts Removal', 'description': 'Laser treatment for wart removal', 'price': 599.00, 'duration': 30, 'category': 'Other Services'},
            
            # Additional IPL Services
            {'name': 'IPL Neck', 'description': 'IPL treatment for neck hair removal', 'price': 499.00, 'duration': 30, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            {'name': 'IPL Arm', 'description': 'IPL treatment for arm hair removal', 'price': 899.00, 'duration': 45, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            
            # Additional Pimple Treatments
            {'name': 'Pimple Injection', 'description': 'Direct injection treatment for pimples', 'price': 299.00, 'duration': 15, 'category': 'Pimple Treatments'},
            
            # Additional Cavitation
            {'name': 'Thighs Cavitation', 'description': 'Non-invasive body contouring for thighs', 'price': 1099.00, 'duration': 60, 'category': 'Body Slimming with Cavitation'},
            
            # Additional IPL Services
            {'name': 'IPL Chest', 'description': 'IPL treatment for chest hair removal', 'price': 999.00, 'duration': 45, 'category': 'Intense Pulsed Light (IPL) Hair Removal'},
            
            # Other Services - Additional
            {'name': 'Korean Lash Lift with Tint', 'description': 'Korean-style lash lift and tint treatment', 'price': 899.00, 'duration': 60, 'category': 'Other Services'},
            {'name': 'Korean Lash Lift without Tint', 'description': 'Korean-style lash lift treatment without tint', 'price': 799.00, 'duration': 60, 'category': 'Other Services'},
        ]
        
        for service_data in services_data:
            category = category_map[service_data['category']]
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

        # Create comprehensive products list
        products_data = [
            {
                'name': 'Derm Options Kojic Soap',
                'description': 'Soap to whiten skin effectively',
                'price': 180.00,
                'stock': 100
            },
            {
                'name': 'Derm Options Pore Minimizer (Toner)',
                'description': 'AB Astringent',
                'price': 380.00,
                'stock': 100
            },
            {
                'name': 'Derm Options Yellow Soap (Anti-Acne)',
                'description': 'Anti-Acne Soap',
                'price': 140.00,
                'stock': 100
            },
            {
                'name': 'Lightening Cream',
                'description': 'For night use.',
                'price': 230.00,
                'stock': 100
            },
            {
                'name': 'Sunscreen Cream',
                'description': 'Apply to help skin fight UV rays.',
                'price': 225.00,
                'stock': 100
            },
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

        # Create comprehensive packages list with all categories
        packages_data = [
            # Whitening Packages
            {
                'name': '3 + 1 Underarm Whitening',
                'description': 'Get 4 sessions for the price of 3',
                'price': 1847.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Back Whitening',
                'description': 'Get 4 back whitening sessions for the price of 3',
                'price': 2397.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Chest Whitening',
                'description': 'Get 4 chest whitening sessions for the price of 3',
                'price': 2097.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            # Facial Packages
            {
                'name': '3 + 1 Diamond Peel',
                'description': 'Get 4 sessions for the price of 3',
                'price': 1697.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Primary Facial',
                'description': 'Get 4 primary facial sessions for the price of 3',
                'price': 1497.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Charcoal Facial',
                'description': 'Get 4 charcoal facial sessions for the price of 3',
                'price': 2097.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Collagen Facial',
                'description': 'Get 4 collagen facial sessions for the price of 3',
                'price': 2397.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            # IPL Packages
            {
                'name': '3 + 1 IPL Underarms',
                'description': 'Get 4 IPL sessions for the price of 3',
                'price': 1497.00,
                'sessions': 4,
                'duration_days': 120,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 IPL Face',
                'description': 'Get 4 IPL face sessions for the price of 3',
                'price': 2697.00,
                'sessions': 4,
                'duration_days': 120,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 IPL Legs',
                'description': 'Get 4 IPL leg sessions for the price of 3',
                'price': 3897.00,
                'sessions': 4,
                'duration_days': 120,
                'grace_period_days': 180
            },
            # Cavitation Packages
            {
                'name': '3 + 1 Arms Cavitation',
                'description': 'Get 4 arms cavitation sessions for the price of 3',
                'price': 2697.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Waist Cavitation',
                'description': 'Get 4 waist cavitation sessions for the price of 3',
                'price': 2997.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Face Cavitation',
                'description': 'Get 4 face cavitation sessions for the price of 3',
                'price': 2397.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            # Laser Packages
            {
                'name': '3 + 1 Pico Glow',
                'description': 'Get 4 Pico Glow laser sessions for the price of 3',
                'price': 5997.00,
                'sessions': 4,
                'duration_days': 120,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Carbon Doll Laser',
                'description': 'Get 4 Carbon Doll Laser sessions for the price of 3',
                'price': 2397.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            # Infusion Packages
            {
                'name': '3 + 1 Geneo Infusion',
                'description': 'Get 4 Geneo Infusion sessions for the price of 3',
                'price': 2997.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
            {
                'name': '3 + 1 Vitamin C Infusion',
                'description': 'Get 4 Vitamin C Infusion sessions for the price of 3',
                'price': 2697.00,
                'sessions': 4,
                'duration_days': 90,
                'grace_period_days': 180
            },
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
            self.style.SUCCESS('Successfully populated database with complete data!')
        )

