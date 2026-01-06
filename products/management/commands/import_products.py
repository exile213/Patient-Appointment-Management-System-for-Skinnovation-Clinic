from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Import products from original data'

    def handle(self, *args, **options):
        # Sample products data matching the original
        products_data = [
            {
                'product_name': 'Derm Options Kojic Soap',
                'description': 'Soap to whiten skin effectively',
                'price': 180.00,
            },
            {
                'product_name': 'Derm Options Pore Minimizer (Toner)',
                'description': 'AB Astringent',
                'price': 380.00,
            },
            {
                'product_name': 'Derm Options Yellow Soap (Anti-Acne)',
                'description': 'Anti-Acne Soap',
                'price': 140.00,
            },
            {
                'product_name': 'Lightening Cream',
                'description': 'For night use.',
                'price': 230.00,
            },
            {
                'product_name': 'Sunscreen Cream',
                'description': 'Apply to help skin fight UV rays.',
                'price': 225.00,
            },
        ]

        for product_data in products_data:
            # Check if product already exists
            existing_products = Product.objects.filter(product_name=product_data['product_name'])
            if existing_products.exists():
                # Update the first one if it exists
                product = existing_products.first()
                product.description = product_data['description']
                product.price = product_data['price']
                product.save()
                self.stdout.write(f'Updated product: {product.product_name}')
            else:
                # Create new product
                product = Product.objects.create(
                    product_name=product_data['product_name'],
                    description=product_data['description'],
                    price=product_data['price'],
                )
                self.stdout.write(f'Created product: {product.product_name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully imported products')
        )
