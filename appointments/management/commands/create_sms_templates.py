from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from appointments.models import SMSTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default SMS templates if they do not exist'

    def handle(self, *args, **options):
        # Get or create a staff user for template creation
        staff_user = User.objects.filter(user_type='staff').first()
        if not staff_user:
            # If no staff, use superuser
            staff_user = User.objects.filter(is_superuser=True).first()
        
        if not staff_user:
            self.stdout.write(self.style.ERROR('No staff or superuser found. Please create one first.'))
            return
        
        # Default templates
        default_templates = [
            {
                'name': 'Default Attendant Reassignment',
                'template_type': 'attendant_reassignment',
                'message': """Hi {patient_name}!

We have assigned a new staff member to assist you for your upcoming appointment:
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}
New Staff: {attendant_name}

If you have any questions, feel free to contact us at {clinic_phone}.
We look forward to seeing you!

- Skinovation Clinic"""
            },
            {
                'name': 'Default Appointment Confirmation',
                'template_type': 'confirmation',
                'message': """Hi {patient_name}!

Your appointment has been confirmed:
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}
Staff: {attendant_name}

We look forward to seeing you!

- Skinovation Clinic"""
            },
            {
                'name': 'Default Appointment Scheduled',
                'template_type': 'scheduled',
                'message': """Hi {patient_name}!

Your appointment has been scheduled and is pending confirmation:
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}

We will confirm your appointment soon!

- Skinovation Clinic"""
            },
            {
                'name': 'Default Cancellation',
                'template_type': 'cancellation',
                'message': """Hi {patient_name}!

Your appointment has been cancelled:
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}

{cancellation_reason}

Please contact us to reschedule.
Thank you for your understanding.

- Skinovation Clinic"""
            }
        ]
        
        created_count = 0
        for template_data in default_templates:
            template, created = SMSTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                name=template_data['name'],
                defaults={
                    'message': template_data['message'],
                    'created_by': staff_user,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template_data["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template_data["name"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal templates created: {created_count}')
        )
