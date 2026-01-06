from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.template_service import template_service

User = get_user_model()

class Command(BaseCommand):
    help = 'Create default SMS templates for the beauty clinic system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the user who will be marked as template creator',
            default='admin'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found. Please provide a valid username.')
            )
            return
        
        # Create default templates
        template_service.create_default_templates(user)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created default SMS templates!')
        )
        
        # Show created templates
        from appointments.models import SMSTemplate
        templates = SMSTemplate.objects.all()
        
        self.stdout.write('\nCreated templates:')
        for template in templates:
            self.stdout.write(f'  - {template.get_template_type_display()}: {template.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal templates created: {templates.count()}')
        )
