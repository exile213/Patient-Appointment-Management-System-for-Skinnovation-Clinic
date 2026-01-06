from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with default credentials'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                user_type='admin'
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created superuser "admin" with password "admin123"')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Superuser "admin" already exists')
            )
