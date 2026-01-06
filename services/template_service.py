from django.conf import settings
from appointments.models import SMSTemplate
from datetime import datetime, date, time
import logging
import re

logger = logging.getLogger(__name__)

class SMSTemplateService:
    """
    Service for managing SMS templates and rendering them with dynamic content
    """
    
    def __init__(self):
        self.clinic_info = {
            'clinic_name': getattr(settings, 'CLINIC_NAME', 'Beauty Clinic'),
            'clinic_phone': getattr(settings, 'CLINIC_PHONE', '09123456789'),
            'clinic_address': getattr(settings, 'CLINIC_ADDRESS', 'Your Clinic Address'),
        }
    
    def get_template(self, template_type, template_name=None):
        """
        Get an active SMS template by type and optionally by name
        
        Args:
            template_type (str): Type of template (confirmation, reminder, etc.)
            template_name (str): Optional specific template name
        
        Returns:
            SMSTemplate: The template object or None if not found
        """
        try:
            if template_name:
                template = SMSTemplate.objects.get(
                    template_type=template_type,
                    name=template_name,
                    is_active=True
                )
            else:
                # Get the first active template of this type
                template = SMSTemplate.objects.filter(
                    template_type=template_type,
                    is_active=True
                ).first()
            
            return template
        except SMSTemplate.DoesNotExist:
            logger.warning(f"No active template found for type: {template_type}, name: {template_name}")
            return None
    
    def _render_message_with_context(self, message, context):
        """Render a raw message string with the provided context using [token] syntax."""
        full_context = {**self.clinic_info}
        if context:
            full_context.update(context)

        def replace_tokens(msg, pattern):
            def _repl(match):
                key = match.group(1)
                return str(full_context.get(key, match.group(0)))
            return pattern.sub(_repl, msg)

        # Preferred [token] syntax for provider, legacy {token} fallback
        message = replace_tokens(message, re.compile(r"\[([A-Za-z0-9_]+)\]"))
        message = replace_tokens(message, re.compile(r"\{([A-Za-z0-9_]+)\}"))
        return message.strip()

    def render_template(self, template, context=None):
        """
        Render a template with the provided context variables
        """
        if not template:
            return ""
        try:
            rendered = self._render_message_with_context(template.message, context)
            return rendered
        except Exception as e:
            logger.error(f"Error rendering template {template.name}: {str(e)}")
            return template.message

    def render_text(self, text, context=None):
        """Render an arbitrary text with context tokens."""
        try:
            rendered = self._render_message_with_context(text, context)
            return rendered
        except Exception as e:
            logger.error(f"Error rendering text: {str(e)}")
            return text
    
    def send_appointment_scheduled(self, appointment, template_name=None):
        """
        Send appointment scheduled SMS
        
        Args:
            appointment: Appointment object
            template_name (str): Not used - transactional messaging
        
        Returns:
            dict: SMS sending result
        """
        # Prepare context variables
        context = self._prepare_appointment_context(appointment)
        
        fallback_message = (
            "Hello [customer_name], your appointment for [service_name] is scheduled on "
            "[appointment_date] at [appointment_time] with [staff_name] in [room_name]. "
            "Thank you! - Skinovation Beauty Clinic"
        )

        rendered_message = self.render_text(fallback_message, context)

        from .sms_service import sms_service
        return sms_service.send_sms(
            appointment.patient.phone,
            message=rendered_message
        )
    
    def send_appointment_confirmation(self, appointment, template_name=None):
        """
        Send appointment confirmation SMS
        
        Args:
            appointment: Appointment object
            template_name (str): Not used - transactional messaging
        
        Returns:
            dict: SMS sending result
        """
        # Prepare context variables
        context = self._prepare_appointment_context(appointment)
        
        fallback_message = (
            "Hello [customer_name], your appointment for [service_name] is confirmed on "
            "[appointment_date] at [appointment_time] with [staff_name] in [room_name]. "
            "Thank you! - Skinovation Beauty Clinic"
        )

        rendered_message = self.render_text(fallback_message, context)

        from .sms_service import sms_service
        return sms_service.send_sms(
            appointment.patient.phone,
            message=rendered_message
        )
    
    def send_appointment_reminder(self, appointment, template_name=None):
        """
        Send appointment reminder SMS
        
        Args:
            appointment: Appointment object
            template_name (str): Not used - transactional messaging
        
        Returns:
            dict: SMS sending result
        """
        # Prepare context variables
        context = self._prepare_appointment_context(appointment)
        
        fallback_message = (
            "Hello [customer_name], reminder: Your appointment for [service_name] is on "
            "[appointment_date] at [appointment_time] with [staff_name] in [room_name]. "
            "Thank you! - Skinovation Beauty Clinic"
        )

        rendered_message = self.render_text(fallback_message, context)

        from .sms_service import sms_service
        return sms_service.send_sms(
            appointment.patient.phone,
            message=rendered_message
        )
    
    def send_two_day_reminder(self, appointment, template_name=None):
        """
        Send 2-day pre-appointment reminder SMS asking patient to confirm attendance
        
        Args:
            appointment: Appointment object
            template_name (str): Not used - transactional messaging
        
        Returns:
            dict: SMS sending result
        """
        # Prepare context variables
        context = self._prepare_appointment_context(appointment)
        
        fallback_message = (
            "Hi [customer_name], reminder: You have an appointment on [appointment_date] at [appointment_time] "
            "for [service_name] with [staff_name]. Please log in to your account to confirm or reschedule. "
            "Visit: skinovation.com"
        )

        rendered_message = self.render_text(fallback_message, context)

        from .sms_service import sms_service
        return sms_service.send_sms(
            appointment.patient.phone,
            message=rendered_message
        )
    
    def send_cancellation_notification(self, appointment, reason="", template_name=None):
        """
        Send cancellation notification SMS
        
        Args:
            appointment: Appointment object
            reason (str): Cancellation reason (optional)
            template_name (str): Not used - transactional messaging
        
        Returns:
            dict: SMS sending result
        """
        # Prepare context variables
        context = self._prepare_appointment_context(appointment)
        
        fallback_message = (
            "Hi [customer_name], your appointment on [appointment_date] at [appointment_time] "
            "for [service_name] with [staff_name] was cancelled."
        )

        rendered_message = self.render_text(fallback_message, context)

        from .sms_service import sms_service
        return sms_service.send_sms(
            appointment.patient.phone,
            message=rendered_message
        )
    
    def send_attendant_reassignment(self, appointment, previous_attendant=None, template_name=None, request=None):
        """
        Send attendant reassignment notification SMS
        
        Args:
            appointment: Appointment object
            previous_attendant: Previous attendant object (optional)
            template_name (str): Not used - transactional messaging
            request: Django request object to build absolute URI (optional)
        
        Returns:
            dict: SMS sending result
        """
        # Prepare context for attendant reassignment
        context = self._prepare_appointment_context(appointment)
        
        # Build portal link for patient to make choice
        portal_link = ""
        if request and hasattr(appointment, 'unavailability_requests'):
            # Get the most recent unavailability request for this appointment
            unavailability_request = appointment.unavailability_requests.filter(
                status='pending',
                pending_reassignment_choice=True
            ).first()
            
            if unavailability_request:
                portal_link = request.build_absolute_uri(
                    f'/appointments/unavailable/{unavailability_request.id}/'
                )
        
        # Enhanced fallback message with portal link
        if portal_link:
            fallback_message = (
                "Hi [customer_name], your attendant is unavailable for your appointment on [appointment_date] at [appointment_time] "
                "for [service_name]. Please log in to your portal to confirm your new attendant or reschedule: " + portal_link
            )
        else:
            fallback_message = (
                "Hi [customer_name], your attendant is unavailable for your appointment on [appointment_date] at [appointment_time] "
                "for [service_name]. Please log in to your portal to confirm your new attendant or reschedule."
            )

        from .sms_service import sms_service
        rendered_message = self.render_text(fallback_message, context)
        return sms_service.send_sms(
            appointment.patient.phone,
            message=rendered_message
        )
    
    def send_package_confirmation(self, package_booking, template_name=None):
        """
        Send package confirmation using template
        
        Args:
            package_booking: Package booking object
            template_name (str): Optional specific template name
        
        Returns:
            dict: SMS sending result
        """
        template = self.get_template('package_confirmation', template_name)
        if not template:
            logger.error("No package confirmation template found")
            return {'success': False, 'error': 'No package confirmation template found'}
        
        # Prepare context variables
        context = self._prepare_package_context(package_booking)
        
        # Render the template
        message = self.render_template(template, context)
        
        # Send SMS
        from .sms_service import sms_service
        return sms_service.send_sms(package_booking.patient.phone, message)
    
    def send_custom_message(self, phone, template_name, context=None):
        """
        Send custom message using a custom template
        
        Args:
            phone (str): Recipient phone number
            template_name (str): Name of the custom template
            context (dict): Variables for the template
        
        Returns:
            dict: SMS sending result
        """
        template = self.get_template('custom', template_name)
        if not template:
            logger.error(f"No custom template found with name: {template_name}")
            return {'success': False, 'error': f'No custom template found: {template_name}'}
        
        # Render the template
        message = self.render_template(template, context or {})
        
        # Send SMS
        from .sms_service import sms_service
        return sms_service.send_sms(phone, message)
    
    def _prepare_appointment_context(self, appointment):
        """
        Prepare context variables for appointment-related templates
        
        Args:
            appointment: Appointment object
        
        Returns:
            dict: Context variables
        """
        # Format date safely - ensure user-friendly format (e.g., "January 28, 2026")
        if isinstance(appointment.appointment_date, date):
            date_str = appointment.appointment_date.strftime('%B %d, %Y')
        else:
            try:
                # Try to parse string date and format it properly
                if isinstance(appointment.appointment_date, str):
                    date_obj = datetime.strptime(appointment.appointment_date, '%Y-%m-%d').date()
                    date_str = date_obj.strftime('%B %d, %Y')
                else:
                    date_str = str(appointment.appointment_date)
            except:
                date_str = str(appointment.appointment_date)
            
        # Format time safely - ensure 12-hour format with AM/PM (e.g., "02:00 PM")
        if isinstance(appointment.appointment_time, time):
            time_str = appointment.appointment_time.strftime('%I:%M %p')
        else:
            try:
                # Try to parse string time and reformat to 12-hour format
                time_str_input = str(appointment.appointment_time)
                # Try common time formats
                for fmt in ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M%p']:
                    try:
                        time_obj = datetime.strptime(time_str_input, fmt).time()
                        time_str = time_obj.strftime('%I:%M %p')
                        break
                    except ValueError:
                        continue
                else:
                    # If all formats fail, use the string as-is
                    time_str = time_str_input
            except:
                # Fallback: use string representation
                time_str = str(appointment.appointment_time)
        
        # Determine service name
        service_name = "Product Purchase"
        if appointment.service:
            service_name = appointment.service.service_name
        elif appointment.package:
            service_name = appointment.package.package_name
        
        if hasattr(appointment, 'attendant') and appointment.attendant:
            attendant_name = f"{appointment.attendant.first_name} {appointment.attendant.last_name}".strip()
        else:
            attendant_name = "our staff"
        
        # Get room information
        if hasattr(appointment, 'room') and appointment.room:
            room_name = f"Room {appointment.room.name}"
        else:
            room_name = "a designated room"
        
        # Get customer name (using patient name)
        customer_name = appointment.patient.get_full_name() or f"{appointment.patient.first_name} {appointment.patient.last_name}".strip()
        
        return {
            'patient_name': customer_name,
            'customer_name': customer_name,  # Alias for compatibility
            'appointment_date': date_str,
            'appointment_time': time_str,
            'service_name': service_name,
            'staff_name': attendant_name,  # Alias for compatibility
            'attendant_name': attendant_name,
            'room_name': room_name,
        }
    
    def _prepare_package_context(self, package_booking):
        """
        Prepare context variables for package-related templates
        
        Args:
            package_booking: Package booking object
        
        Returns:
            dict: Context variables
        """
        return {
            'patient_name': package_booking.patient.get_full_name(),
            'package_name': package_booking.package.package_name,
            'package_price': f"P{package_booking.package.price:,.2f}",
            'package_sessions': package_booking.package.sessions,
            'package_duration': f"{package_booking.package.duration_days} days",
        }
    
    def create_default_templates(self, user):
        """
        Create default SMS templates if none exist
        
        Args:
            user: User who will be marked as creator
        """
        default_templates = [
            {
                'name': 'Default Scheduled',
                'template_type': 'scheduled',
                'message': """Hi {patient_name}!

Thank you! Your appointment has been scheduled and is now being processed.

Appointment Details:
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}

Please await confirmation as our staff will personally review the details of your appointment and will send you a final confirmation shortly which will include all the necessary information.

Please keep an eye on your inbox for that update!

- Skinovation Clinic"""
            },
            {
                'name': 'Default Confirmation',
                'template_type': 'confirmation',
                'message': """Hi {patient_name}!

Your appointment has been confirmed!

Appointment Details:
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}
Attendant: {attendant_name}
Location: {clinic_name}

Please arrive 15 minutes early.
Thank you for choosing us!

- Skinovation Clinic"""
            },
            {
                'name': 'Default Reminder',
                'template_type': 'reminder',
                'message': """Hi {patient_name}!

Reminder: You have an appointment tomorrow:
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}

Please arrive 15 minutes early.
See you soon!

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
            },
            {
                'name': 'Default Package Confirmation',
                'template_type': 'package_confirmation',
                'message': """Hi {patient_name}!

Your package has been booked successfully:
Package: {package_name}
Price: {package_price}
Sessions: {package_sessions}
Duration: {package_duration}

Your package is now active. Book your sessions anytime!
Thank you for choosing us!

- Skinovation Clinic"""
            },
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
                'name': 'Default Attendant Assignment',
                'template_type': 'attendant_assignment',
                'message': """Hi {attendant_name}!

An appointment has been assigned to you.

Appointment Details:
Patient: {patient_name}
Date: {appointment_date}
Time: {appointment_time}
Service: {service_name}

Please check your attendant portal for complete details.

- Skinovation Clinic"""
            }
        ]
        
        for template_data in default_templates:
            if not SMSTemplate.objects.filter(
                template_type=template_data['template_type'],
                name=template_data['name']
            ).exists():
                SMSTemplate.objects.create(
                    name=template_data['name'],
                    template_type=template_data['template_type'],
                    message=template_data['message'],
                    created_by=user
                )
                logger.info(f"Created default template: {template_data['name']}")

# Global template service instance
template_service = SMSTemplateService()
