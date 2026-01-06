from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from services.utils import send_appointment_sms

class Command(BaseCommand):
    help = 'Send SMS reminders for appointments scheduled for tomorrow'

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
            if appointment.patient.phone:
                sms_result = send_appointment_sms(appointment, 'reminder')
                if sms_result['success']:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Reminder sent to {appointment.patient.full_name} for {appointment.appointment_date}'
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to send reminder to {appointment.patient.full_name}: {sms_result.get("error", "Unknown error")}'
                        )
                    )
            else:
                failed_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'No phone number for {appointment.patient.full_name}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Reminder sending completed. Sent: {sent_count}, Failed: {failed_count}'
            )
        )
