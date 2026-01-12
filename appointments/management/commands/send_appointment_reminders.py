from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from appointments.models import Appointment, SMSReminder
from services.utils import send_appointment_sms, send_sms_notification
from services.template_service import template_service
from django.conf import settings

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
        # Get current time in local timezone (Asia/Manila) for date comparisons
        # This ensures appointment_date comparisons use the same timezone as appointments are stored
        # Django stores dates in local timezone, so we need to convert UTC now to local timezone
        now_utc = timezone.now()
        # Use Django's timezone utilities (works with USE_TZ=True)
        # timezone.get_current_timezone() returns the timezone from settings.TIME_ZONE
        now = timezone.localtime(now_utc)
        
        # Debug: Show both UTC and local time for troubleshooting
        self.stdout.write(f'DEBUG: UTC time: {now_utc}')
        self.stdout.write(f'DEBUG: Local timezone: {settings.TIME_ZONE}')
        self.stdout.write(f'DEBUG: Local time: {now}')
        self.stdout.write(f'DEBUG: UTC date: {now_utc.date()}, Local date: {now.date()}')
        
        # Write initial debug message to confirm command is running
        self.stdout.write('='*60)
        self.stdout.write('APPOINTMENT REMINDER COMMAND STARTED')
        self.stdout.write(f'Filter: {filter_type}')
        self.stdout.write(f'Server Time: {now}')
        self.stdout.write('='*60)
        
        # Check SMS configuration
        sms_enabled = getattr(settings, 'SMS_ENABLED', False)
        sms_api_key = getattr(settings, 'SKYSMS_API_KEY', '')
        
        if not sms_enabled:
            self.stdout.write(
                self.style.ERROR(
                    '⚠️  WARNING: SMS_ENABLED is False. SMS reminders will not be sent!'
                )
            )
        if not sms_api_key:
            self.stdout.write(
                self.style.ERROR(
                    '⚠️  WARNING: SKYSMS_API_KEY is not set. SMS reminders will fail!'
                )
            )
        
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
            self.stdout.write(f'\nDEBUG: Current server time: {now}')
            self.stdout.write(f'DEBUG: Current date: {now.date()}')
            self.stdout.write(f'DEBUG: Current time: {now.time()}')
            
            # Get all appointments for today first (without status filter to see what exists)
            all_today_appointments = Appointment.objects.filter(
                appointment_date=now.date()
            )
            self.stdout.write(f'\nDEBUG: ==========================================')
            self.stdout.write(f'DEBUG: QUERY ANALYSIS')
            self.stdout.write(f'DEBUG: ==========================================')
            self.stdout.write(f'DEBUG: Current server time: {now}')
            self.stdout.write(f'DEBUG: Current date: {now.date()}')
            self.stdout.write(f'DEBUG: Current time: {now.time()}')
            self.stdout.write(f'DEBUG: Timezone: {timezone.get_current_timezone()}')
            self.stdout.write(f'DEBUG: Total appointments for today (any status): {all_today_appointments.count()}')
            
            # Show all appointments for debugging
            if all_today_appointments.count() > 0:
                self.stdout.write(f'\nDEBUG: All appointments for today:')
                for apt in all_today_appointments:
                    patient_name = apt.patient.get_full_name() if apt.patient else "NO PATIENT"
                    self.stdout.write(
                        f'  - Appointment #{apt.id}: '
                        f'Status={apt.status}, '
                        f'Date={apt.appointment_date}, '
                        f'Time={apt.appointment_time}, '
                        f'Patient={patient_name}, '
                        f'Service={apt.get_service_name()}'
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'\n⚠️  NO APPOINTMENTS FOUND FOR TODAY ({now.date()})'
                    )
                )
                self.stdout.write(
                    f'   → Check if appointment date matches today\'s date'
                )
                self.stdout.write(
                    f'   → Check if appointment exists in database'
                )
            
            # Now filter by status
            appointments = Appointment.objects.filter(
                appointment_date=now.date(),
                status__in=['confirmed', 'scheduled']
            )
            
            self.stdout.write(f'\nDEBUG: Appointments with status confirmed/scheduled: {appointments.count()}')
            
            if appointments.count() == 0 and all_today_appointments.count() > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠️  WARNING: Found {all_today_appointments.count()} appointments for today, '
                        f'but NONE have status "confirmed" or "scheduled"'
                    )
                )
                self.stdout.write(f'   → Check appointment statuses in the list above')
            
            # Filter appointments that are approximately 1 hour away
            filtered_appointments = []
            for apt in appointments:
                # Combine appointment date and time into datetime
                # Use the same timezone as 'now' to avoid timezone mismatches
                naive_datetime = datetime.combine(apt.appointment_date, apt.appointment_time)
                
                # Check if 'now' is timezone-aware to determine how to make appointment datetime
                if timezone.is_aware(now):
                    # Use the same timezone as 'now'
                    appointment_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
                else:
                    # If now is naive, make appointment naive too
                    appointment_datetime = naive_datetime
                
                # Check if appointment is between 50-70 minutes away (expanded window for 15-min cron)
                time_diff = (appointment_datetime - now).total_seconds() / 60
                self.stdout.write(
                    f'\nDEBUG: Appointment #{apt.id}:'
                )
                self.stdout.write(f'  - Patient: {apt.patient.get_full_name() if apt.patient else "None"}')
                self.stdout.write(f'  - Appointment time: {apt.appointment_time}')
                self.stdout.write(f'  - Appointment datetime: {appointment_datetime}')
                self.stdout.write(f'  - Current datetime: {now}')
                self.stdout.write(f'  - Time difference: {time_diff:.1f} minutes')
                
                # Expanded window: 45-75 minutes (to account for 15-minute cron intervals)
                # This ensures we catch appointments even if cron runs slightly early/late
                # With 15-min intervals, this window ensures we catch appointments reliably
                if 45 <= time_diff <= 75:
                    filtered_appointments.append(apt)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ WITHIN WINDOW (45-75 min) - WILL PROCESS'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ✗ OUTSIDE WINDOW (needs 45-75 min, got {time_diff:.1f} min) - SKIPPED'
                        )
                    )
            
            appointments = filtered_appointments
            self.stdout.write(f'\nDEBUG: Final filtered appointments (within 45-75 min window): {len(appointments)}')
            reminder_type = 'reminder'
            reminder_type_db = 'one_hour'
            message_suffix = "(1 hour before)"
        
        sent_count = 0
        failed_count = 0
        skipped_count = 0
        already_sent_count = 0
        
        for appointment in appointments:
            # Validate appointment has all required fields
            if not appointment.patient:
                skipped_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Appointment #{appointment.id} has no patient assigned - SKIPPED'
                    )
                )
                continue
            
            if not appointment.attendant:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Appointment #{appointment.id} has no attendant assigned - SKIPPED'
                    )
                )
                continue
            
            # Check if patient has phone number
            if not appointment.patient.phone:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'No phone number for {appointment.patient.get_full_name()} (Appointment #{appointment.id}) - SKIPPED'
                    )
                )
                continue
            
            # Check if appointment has at least one service/product/package
            if not appointment.service and not appointment.product and not appointment.package:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Appointment #{appointment.id} has no service/product/package assigned - SKIPPED'
                    )
                )
                continue
            
            self.stdout.write(
                f'DEBUG: Processing Appointment #{appointment.id} - '
                f'Patient: {appointment.patient.get_full_name()}, '
                f'Phone: {appointment.patient.phone}, '
                f'Service: {appointment.get_service_name()}, '
                f'Status: {appointment.status}'
            )
            
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
            
            # Send SMS reminder - use same direct method as admin SMS test page
            # But use template service to format the message properly
            self.stdout.write(
                f'DEBUG: Sending SMS to {appointment.patient.get_full_name()} '
                f'({appointment.patient.phone}) - Reminder type: {reminder_type}'
            )
            
            try:
                if reminder_type == 'two_day_reminder':
                    # Use template service method for 2-day reminder
                    sms_result = template_service.send_two_day_reminder(appointment)
                else:
                    # Use template service method for regular reminder (1day or 1hour)
                    sms_result = template_service.send_appointment_reminder(appointment)
                
                # Debug: Show SMS result
                self.stdout.write(f'DEBUG: Template service SMS result: {sms_result}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Exception in template service: {str(e)}'
                    )
                )
                sms_result = {'success': False, 'error': str(e)}
            
            # If template service fails, fall back to direct SMS (like admin test page)
            if not sms_result.get('success'):
                self.stdout.write(
                    self.style.WARNING(
                        f'  → Template service failed, trying fallback method...'
                    )
                )
                # Prepare simple message as fallback
                context = template_service._prepare_appointment_context(appointment)
                if reminder_type == 'two_day_reminder':
                    message = (
                        f"Hi {context.get('customer_name', 'Customer')}, reminder: You have an appointment on "
                        f"{context.get('appointment_date', '')} at {context.get('appointment_time', '')} "
                        f"for {context.get('service_name', 'service')}. Please log in to confirm or reschedule. "
                        f"- Skinovation Beauty Clinic. This is an automated message please don't reply"
                    )
                else:
                    message = (
                        f"Hello {context.get('customer_name', 'Customer')}, reminder: Your appointment for "
                        f"{context.get('service_name', 'service')} is on {context.get('appointment_date', '')} "
                        f"at {context.get('appointment_time', '')}. Thank you! - Skinovation Beauty Clinic. "
                        f"This is an automated message please don't reply"
                    )
                
                # Use the same SMS sending method as admin test page
                sms_result = send_sms_notification(
                    appointment.patient.phone,
                    message,
                    user=None
                )
                self.stdout.write(f'DEBUG: Fallback SMS result: {sms_result}')
            
            patient_sms_sent = sms_result.get('success', False)
            self.stdout.write(f'DEBUG: Final SMS success status: {patient_sms_sent}')
            
            if patient_sms_sent:
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
                        f'({appointment.patient.phone}) for {appointment.appointment_date} at {appointment.appointment_time} '
                        f'{message_suffix}'
                    )
                )
            else:
                failed_count += 1
                error_msg = sms_result.get('error') or sms_result.get('message', 'Unknown error')
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed to send to {appointment.patient.get_full_name()} ({appointment.patient.phone}): {error_msg}'
                    )
                )
                # Log additional debug info
                if 'SMS notifications are disabled' in str(error_msg):
                    self.stdout.write(
                        self.style.ERROR(
                            '  → SMS_ENABLED is False or SKYSMS_API_KEY is missing in settings'
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
