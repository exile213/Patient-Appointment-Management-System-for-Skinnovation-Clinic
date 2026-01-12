from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from appointments.models import Appointment, SMSReminder
from services.utils import send_appointment_sms

class Command(BaseCommand):
    help = 'Send appointment reminders based on specified time filter (2days, 1day, 1hour)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filter',
            type=str,
            choices=['2days', '1day', '1hour'],
            required=True,
            help='Time filter for reminders: 2days, 1day, or 1hour before appointment'
        )

    def handle(self, *args, **options):
        filter_type = options['filter']
        now = timezone.now()
        
        # Determine target appointments based on filter
        if filter_type == '2days':
            target_date = (now + timedelta(days=2)).date()
            appointments = Appointment.objects.filter(
                appointment_date=target_date,
                status__in=['confirmed', 'scheduled']
            )
            reminder_type = 'two_day_reminder'
            reminder_type_db = 'two_day'
            message_suffix = "(2 days before)"
            
        elif filter_type == '1day':
            target_date = (now + timedelta(days=1)).date()
            appointments = Appointment.objects.filter(
                appointment_date=target_date,
                status__in=['confirmed', 'scheduled']
            )
            reminder_type = 'reminder'
            reminder_type_db = 'one_day'
            message_suffix = "(1 day before)"
            
        elif filter_type == '1hour':
            # For 1 hour before, check appointments happening in the next hour
            appointments = Appointment.objects.filter(
                appointment_date=now.date(),
                status__in=['confirmed', 'scheduled']
            )
            
            # Filter appointments that are approximately 1 hour away
            filtered_appointments = []
            for apt in appointments:
                # Combine appointment date and time into datetime
                appointment_datetime = timezone.make_aware(
                    datetime.combine(apt.appointment_date, apt.appointment_time)
                )
                
                # Check if appointment is between 55-65 minutes away (to avoid multiple sends)
                time_diff = (appointment_datetime - now).total_seconds() / 60
                if 55 <= time_diff <= 65:
                    filtered_appointments.append(apt)
            
            appointments = filtered_appointments
            reminder_type = 'reminder'
            reminder_type_db = 'one_hour'
            message_suffix = "(1 hour before)"
        
        sent_count = 0
        failed_count = 0
        skipped_count = 0
        already_sent_count = 0
        
        for appointment in appointments:
            # Check if patient has phone number
            if not appointment.patient.phone:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'No phone number for {appointment.patient.get_full_name()} - Appointment #{appointment.id}'
                    )
                )
                continue
            
            # Check if reminder has already been sent (idempotency check)
            existing_reminder = SMSReminder.objects.filter(
                appointment=appointment,
                reminder_type=reminder_type_db,
                sent=True
            ).first()
            
            if existing_reminder:
                already_sent_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'⊘ Reminder already sent to {appointment.patient.get_full_name()} '
                        f'for {appointment.appointment_date} at {appointment.appointment_time} '
                        f'{message_suffix} (sent at {existing_reminder.sent_at})'
                    )
                )
                continue
            
            # Send SMS reminder
            sms_result = send_appointment_sms(appointment, reminder_type)
            
            if sms_result['success']:
                # Record that the reminder was sent
                SMSReminder.objects.update_or_create(
                    appointment=appointment,
                    reminder_type=reminder_type_db,
                    defaults={
                        'sent': True,
                        'sent_at': timezone.now()
                    }
                )
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Reminder sent to {appointment.patient.get_full_name()} '
                        f'for {appointment.appointment_date} at {appointment.appointment_time} '
                        f'{message_suffix}'
                    )
                )
            else:
                failed_count += 1
                error_msg = sms_result.get('error', 'Unknown error')
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed to send to {appointment.patient.get_full_name()}: {error_msg}'
                    )
                )
        
        # Summary
        total_processed = sent_count + failed_count + skipped_count + already_sent_count
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Reminder Sending Completed - Filter: {filter_type}'
            )
        )
        self.stdout.write(f'  Total Processed: {total_processed}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Sent Successfully: {sent_count}'))
        if already_sent_count > 0:
            self.stdout.write(self.style.WARNING(f'  ⊘ Already Sent (Skipped): {already_sent_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {failed_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'  ⊘ Skipped (No Phone): {skipped_count}'))
        self.stdout.write('='*60)
