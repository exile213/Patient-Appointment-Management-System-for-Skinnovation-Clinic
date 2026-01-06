from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment, SMSReminder
from services.utils import send_appointment_sms


class Command(BaseCommand):
    help = 'Send SMS reminders 2 days before scheduled appointments asking patients to confirm or reschedule'

    def handle(self, *args, **options):
        # Get the date 2 days from now
        reminder_date = timezone.now().date() + timedelta(days=2)
        
        # Get confirmed and scheduled appointments for 2 days from now
        appointments = Appointment.objects.filter(
            appointment_date=reminder_date,
            status__in=['confirmed', 'scheduled']
        )
        
        sent_count = 0
        failed_count = 0
        skipped_count = 0
        
        for appointment in appointments:
            # Check if we've already sent a 2-day reminder for this appointment
            existing_reminder = SMSReminder.objects.filter(
                appointment=appointment,
                reminder_type='two_day',
                sent=True
            ).first()
            
            if existing_reminder:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'2-day reminder already sent for {appointment.patient.get_full_name()} - {appointment.appointment_date}'
                    )
                )
                continue
            
            if appointment.patient.phone:
                # Send 2-day reminder SMS
                sms_result = send_appointment_sms(appointment, 'two_day_reminder')
                
                if sms_result['success']:
                    # Record that the reminder was sent
                    SMSReminder.objects.update_or_create(
                        appointment=appointment,
                        reminder_type='two_day',
                        defaults={'sent': True, 'sent_at': timezone.now()}
                    )
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'2-day reminder sent to {appointment.patient.get_full_name()} for {appointment.appointment_date}'
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to send 2-day reminder to {appointment.patient.get_full_name()}: {sms_result.get("error", "Unknown error")}'
                        )
                    )
            else:
                failed_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'No phone number for {appointment.patient.get_full_name()}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n2-Day Reminder sending completed:\n'
                f'  Sent: {sent_count}\n'
                f'  Failed: {failed_count}\n'
                f'  Skipped: {skipped_count}'
            )
        )
