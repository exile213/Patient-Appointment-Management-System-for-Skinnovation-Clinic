from django.core.management.base import BaseCommand
from services.models import Service, ServiceCategory
import re

class Command(BaseCommand):
    help = 'Import services and categories from SQL data'

    def handle(self, *args, **options):
        # Create service categories
        categories_data = [
            (1, 'Facials'),
            (2, 'Anti-Aging & Face Lift'),
            (3, 'Pico Laser'),
            (4, 'Lightening Treatments'),
            (5, 'Pimple Treatments'),
            (6, 'Body Slimming with Cavitation'),
            (7, 'Hair Removal (IPL)'),
            (8, 'Other Services'),
        ]
        
        for cat_id, name in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                id=cat_id,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f'Created category: {name}')
            else:
                self.stdout.write(f'Category already exists: {name}')

        # Sample services data
        services_data = [
            (1, 'Primary Facial (Face)', 'A comprehensive facial treatment for the face area', 499.00, 60, 1),
            (2, 'Chest/Back', 'A facial treatment specifically for the chest or back area', 649.00, 60, 1),
            (3, 'Neck', 'A facial treatment targeting the neck area', 449.00, 60, 1),
            (4, 'Charcoal', 'A facial that includes a Diamond Peel and a Charcoal mask for deep cleansing and purification', 699.00, 60, 1),
            (5, 'Diamond Peel', 'Exfoliating facial treatment using diamond-tipped wand', 599.00, 60, 1),
            (6, 'Collagen', 'Anti-aging facial treatment with collagen infusion', 799.00, 90, 2),
            (7, 'Anti-Acne Treatment', 'Specialized treatment for acne-prone skin', 699.00, 60, 5),
            (8, 'IPL Face', 'Intense Pulsed Light treatment for facial hair removal', 899.00, 45, 7),
            (9, 'IPL Underarms', 'IPL treatment for underarm hair removal', 499.00, 30, 7),
            (10, 'IPL Legs', 'IPL treatment for leg hair removal', 1299.00, 60, 7),
            (11, 'Arms Cavitation', 'Non-invasive body contouring for arms', 899.00, 60, 6),
            (12, 'Waist Cavitation', 'Non-invasive body contouring for waist area', 999.00, 60, 6),
            (13, 'Back Whitening', 'Skin lightening treatment for back area', 799.00, 60, 4),
            (14, 'Underarm Whitening', 'Skin lightening treatment for underarms', 599.00, 45, 4),
            (15, 'Chest Whitening', 'Skin lightening treatment for chest area', 699.00, 60, 4),
        ]

        for service_id, name, description, price, duration, category_id in services_data:
            try:
                category = ServiceCategory.objects.get(id=category_id)
                service, created = Service.objects.get_or_create(
                    id=service_id,
                    defaults={
                        'service_name': name,
                        'description': description,
                        'price': price,
                        'duration': duration,
                        'category': category,
                    }
                )
                if created:
                    self.stdout.write(f'Created service: {name}')
                else:
                    self.stdout.write(f'Service already exists: {name}')
            except ServiceCategory.DoesNotExist:
                self.stdout.write(f'Category {category_id} not found for service {name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully imported services and categories')
        )
