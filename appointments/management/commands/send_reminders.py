from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from utils.notifications import send_appointment_notification

class Command(BaseCommand):
    help = 'Send email and SMS reminders for appointments scheduled for tomorrow'

    def handle(self, *args, **options):
        # Get tomorrow's date
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Get confirmed and scheduled appointments for tomorrow
        # Send reminders for both confirmed and scheduled appointments
        appointments = Appointment.objects.filter(
            appointment_date=tomorrow,
            status__in=['confirmed', 'scheduled']
        )
        
        sent_count = 0
        failed_count = 0
        
        for appointment in appointments:
            # Send unified notification (both email and SMS simultaneously)
            notification_result = send_appointment_notification(appointment, 'reminder')
            email_sent = notification_result.get('email_sent', False)
            sms_sent = notification_result.get('sms_sent', False)
            
            if email_sent or sms_sent:
                sent_count += 1
                notification_types = []
                if email_sent:
                    notification_types.append('Email')
                if sms_sent:
                    notification_types.append('SMS')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Reminder sent via {", ".join(notification_types)} to {appointment.patient.full_name} for {appointment.appointment_date}'
                    )
                )
            else:
                failed_count += 1
                errors = '; '.join(notification_result.get('errors', ['Unknown error']))
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send reminder to {appointment.patient.full_name}: {errors}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Reminder sending completed. Sent: {sent_count}, Failed: {failed_count}'
            )
        )
