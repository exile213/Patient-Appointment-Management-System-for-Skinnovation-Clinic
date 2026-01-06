from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Clean up duplicate products'

    def handle(self, *args, **options):
        # Get all products
        products = Product.objects.all()
        
        # Find duplicates by name
        seen_names = set()
        duplicates = []
        
        for product in products:
            if product.product_name in seen_names:
                duplicates.append(product)
            else:
                seen_names.add(product.product_name)
        
        # Remove duplicates (keep the first one)
        for duplicate in duplicates:
            self.stdout.write(f'Removing duplicate: {duplicate.product_name} (ID: {duplicate.id})')
            duplicate.delete()
        
        if duplicates:
            self.stdout.write(f'Removed {len(duplicates)} duplicate products')
        else:
            self.stdout.write('No duplicate products found')
        
        # List remaining products
        remaining_products = Product.objects.all()
        self.stdout.write('\nRemaining products:')
        for product in remaining_products:
            self.stdout.write(f'- {product.product_name} (ID: {product.id})')
        
        self.stdout.write(
            self.style.SUCCESS('Product cleanup complete')
        )
