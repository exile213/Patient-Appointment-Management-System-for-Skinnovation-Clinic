from django.conf import settings
from .sms_service import sms_service
import logging

logger = logging.getLogger(__name__)

def send_sms_notification(phone, message, sender_id=None, user=None):
    """
    Utility function to send SMS notifications
    
    Args:
        phone (str): Recipient's phone number
        message (str): SMS message content
        sender_id (str): Optional sender ID override
        user (User): User who sent the SMS (for history tracking)
    
    Returns:
        dict: SMS sending result
    """
    if not getattr(settings, 'SMS_ENABLED', True):
        logger.info("SMS notifications are disabled")
        return {
            'success': False,
            'message': 'SMS notifications are disabled'
        }
    
    try:
        sender = sender_id or getattr(settings, 'SMS_SENDER_ID', 'BEAUTY')
        result = sms_service.send_sms(
            phone,
            message,
            sender
        )
        
        # Save to SMS history if user is provided
        if user:
            from appointments.models import SMSHistory
            SMSHistory.objects.create(
                sender=user,
                phone_number=phone,
                message=message,
                status='sent' if result['success'] else 'failed',
                message_id=result.get('message_id'),
                api_response=result
            )
        
        if result['success']:
            logger.info(f"SMS sent successfully to {phone}")
        else:
            logger.error(f"Failed to send SMS to {phone}: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending SMS to {phone}: {str(e)}")
        
        # Save failed attempt to history if user is provided
        if user:
            from appointments.models import SMSHistory
            SMSHistory.objects.create(
                sender=user,
                phone_number=phone,
                message=message,
                status='failed',
                api_response={'error': str(e)}
            )
        
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to send SMS notification'
        }

def send_appointment_sms(appointment, sms_type='confirmation', **kwargs):
    """
    Send appointment-related SMS notifications
    
    Args:
        appointment: Appointment object
        sms_type (str): Type of SMS ('scheduled', 'confirmation', 'reminder', 'two_day_reminder', 'cancellation', 'reassignment')
    
    Returns:
        dict: SMS sending result
    """
    if not appointment.patient.phone:
        logger.warning(f"Cannot send SMS to patient {appointment.patient.get_full_name()}: Phone number not available")
        return {
            'success': False,
            'error': 'Patient phone number not available',
            'message': 'Patient phone number not available'
        }
    
    try:
        if sms_type == 'scheduled':
            result = sms_service.send_appointment_scheduled(appointment)
        elif sms_type == 'confirmation':
            result = sms_service.send_appointment_confirmation(appointment)
        elif sms_type == 'reminder':
            result = sms_service.send_appointment_reminder(appointment)
        elif sms_type == 'two_day_reminder':
            result = sms_service.send_two_day_reminder(appointment)
        elif sms_type == 'cancellation':
            result = sms_service.send_cancellation_notification(appointment)
        elif sms_type in ['reassignment', 'attendant_reassignment']:
            result = sms_service.send_attendant_reassignment(
                appointment,
                previous_attendant=kwargs.get('previous_attendant')
            )
        else:
            return {
                'success': False,
                'message': f'Unknown SMS type: {sms_type}'
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending appointment SMS: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to send appointment SMS'
        }

def send_package_sms(package_booking):
    """
    Send package booking confirmation SMS
    
    Args:
        package_booking: Package booking object
    
    Returns:
        dict: SMS sending result
    """
    if not package_booking.patient.phone:
        return {
            'success': False,
            'message': 'Patient phone number not available'
        }
    
    try:
        result = sms_service.send_package_confirmation(package_booking)
        return result
        
    except Exception as e:
        logger.error(f"Error sending package SMS: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to send package SMS'
        }

def send_attendant_assignment_sms(appointment):
    """
    Send SMS to attendant when an appointment is assigned to them
    
    Args:
        appointment: Appointment object
    
    Returns:
        dict: SMS sending result
    """
    try:
        # Get attendant user
        from accounts.models import User
        attendant_user = User.objects.filter(
            user_type='attendant',
            first_name=appointment.attendant.first_name,
            last_name=appointment.attendant.last_name,
            is_active=True
        ).first()
        
        if not attendant_user:
            return {
                'success': False,
                'message': 'Attendant user not found'
            }
        
        # Get attendant profile for phone number
        profile = getattr(attendant_user, 'attendant_profile', None)
        if not profile or not profile.phone:
            return {
                'success': False,
                'message': 'Attendant phone number not available'
            }
        
        # Format message with attendant name
        attendant_name = attendant_user.get_full_name() or f"{attendant_user.first_name} {attendant_user.last_name}"
        service_name = appointment.get_service_name()
        message = (
            f"Hi {attendant_name}, you have been assigned a new appointment. "
            f"Patient: {appointment.patient.get_full_name()}, "
            f"Service: {service_name}, "
            f"Date: {appointment.appointment_date.strftime('%B %d, %Y')}, "
            f"Time: {appointment.appointment_time.strftime('%I:%M %p')}. "
            f"Please check your attendant portal for details."
        )
        
        result = send_sms_notification(profile.phone, message, user=attendant_user)
        return result
        
    except Exception as e:
        logger.error(f"Error sending attendant assignment SMS: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to send attendant assignment SMS'
        }
