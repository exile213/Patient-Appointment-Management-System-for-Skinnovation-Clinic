"""
Email and notification utilities for patient communications
Sends appointment-related notifications via email to patients
"""
import logging
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime

logger = logging.getLogger(__name__)


def send_appointment_email(appointment, email_type='confirmation'):
    """
    Send appointment-related email notifications to patient
    
    Args:
        appointment: Appointment object
        email_type (str): Type of email - 'confirmation', 'reminder', 'cancellation', 'rescheduled', 'reassignment'
    
    Returns:
        dict: Email sending result with success status
    """
    
    if not appointment.patient or not appointment.patient.email:
        logger.warning(f"Cannot send email to appointment {appointment.id}: Patient email not available")
        return {
            'success': False,
            'message': 'Patient email not available'
        }
    
    try:
        # Import here to avoid circular imports
        from accounts.email_service import MailtrapEmailService
        
        email_service = MailtrapEmailService()
        patient = appointment.patient
        
        # Prepare context for email template
        context = {
            'patient_name': patient.get_full_name(),
            'first_name': patient.first_name,
            'appointment_date': appointment.appointment_date.strftime('%B %d, %Y') if appointment.appointment_date else 'N/A',
            'appointment_time': appointment.appointment_time.strftime('%I:%M %p') if appointment.appointment_time else 'N/A',
            'appointment_id': appointment.id,
            'service_name': appointment.service.service_name if appointment.service else 'Service',
            'attendant_name': f"{appointment.attendant.first_name} {appointment.attendant.last_name}" if appointment.attendant else 'Staff',
            'clinic_name': 'Skinnovation Beauty Clinic',
        }
        
        # Define email templates and subjects
        email_configs = {
            'confirmation': {
                'subject': 'Appointment Confirmation - Skinnovation Beauty Clinic',
                'body': _get_confirmation_email_html(context)
            },
            'reminder': {
                'subject': 'Appointment Reminder - Skinnovation Beauty Clinic',
                'body': _get_reminder_email_html(context)
            },
            'cancellation': {
                'subject': 'Appointment Cancelled - Skinnovation Beauty Clinic',
                'body': _get_cancellation_email_html(context)
            },
            'rescheduled': {
                'subject': 'Appointment Rescheduled - Skinnovation Beauty Clinic',
                'body': _get_rescheduled_email_html(context)
            },
            'reassignment': {
                'subject': 'Attendant Reassignment - Skinnovation Beauty Clinic',
                'body': _get_reassignment_email_html(context)
            },
        }
        
        config = email_configs.get(email_type, email_configs['confirmation'])
        
        # Send email using Mailtrap
        import mailtrap as mt
        
        mail = mt.Mail(
            sender=mt.Address(
                email="noreply@skinovation.com",
                name="Skinnovation Beauty Clinic"
            ),
            to=[mt.Address(email=patient.email, name=patient.get_full_name())],
            subject=config['subject'],
            html=config['body'],
            text=_strip_html_tags(config['body']),
            category=f"Appointment-{email_type.capitalize()}",
        )
        
        response = email_service.client.send(mail)
        logger.info(f"Appointment email ({email_type}) sent to {patient.email}")
        
        return {
            'success': True,
            'message': f'Appointment {email_type} email sent successfully!',
            'response': response
        }
        
    except Exception as e:
        logger.error(f"Error sending appointment email ({email_type}): {str(e)}")
        return {
            'success': False,
            'message': f'Failed to send appointment email: {str(e)}',
            'error': str(e)
        }


def _get_confirmation_email_html(context):
    """Generate HTML for appointment confirmation email"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">✓ Appointment Confirmed</h1>
                </div>
                <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Dear <strong>{context['first_name']}</strong>,</p>
                    <p>Your appointment has been confirmed! Here are your appointment details:</p>
                    
                    <div style="background-color: #e8f4f8; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; border-radius: 5px;">
                        <p><strong>📅 Date:</strong> {context['appointment_date']}</p>
                        <p><strong>🕐 Time:</strong> {context['appointment_time']}</p>
                        <p><strong>💆 Service:</strong> {context['service_name']}</p>
                        <p><strong>👨‍⚕️ Attendant:</strong> {context['attendant_name']}</p>
                        <p><strong>Confirmation ID:</strong> #{context['appointment_id']}</p>
                    </div>
                    
                    <h2 style="color: #667eea; font-size: 18px; margin-top: 25px;">Important Reminders:</h2>
                    <ul style="line-height: 1.8;">
                        <li>Please arrive 10 minutes earlier than your appointment time</li>
                        <li>If you need to reschedule or cancel, please notify us at least 24 hours in advance</li>
                        <li>Bring any relevant medical documents if it's your first visit with our clinic</li>
                        <li>Please keep your phone with you in case we need to reach you</li>
                    </ul>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>❓ Questions?</strong> Feel free to reply to this email or call us at the clinic. Our team is here to help!</p>
                    </div>
                    
                    <p style="margin-top: 25px; color: #666;">Thank you for choosing {context['clinic_name']}!</p>
                    <p style="color: #666;"><strong>Best regards,</strong><br>The {context['clinic_name']} Team</p>
                </div>
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #999;">
                    <p style="margin: 0;">© 2024 {context['clinic_name']}. All rights reserved.<br>This is an automated email. Please do not reply directly.</p>
                </div>
            </div>
        </body>
    </html>
    """


def _get_reminder_email_html(context):
    """Generate HTML for appointment reminder email"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">🔔 Appointment Reminder</h1>
                </div>
                <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hi <strong>{context['first_name']}</strong>,</p>
                    <p>This is a friendly reminder about your upcoming appointment:</p>
                    
                    <div style="background-color: #fff8e1; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 5px;">
                        <p><strong>📅 Date:</strong> {context['appointment_date']}</p>
                        <p><strong>🕐 Time:</strong> {context['appointment_time']}</p>
                        <p><strong>💆 Service:</strong> {context['service_name']}</p>
                        <p><strong>👨‍⚕️ Attendant:</strong> {context['attendant_name']}</p>
                    </div>
                    
                    <p>Please arrive on time. If you need to cancel or reschedule, please let us know as soon as possible.</p>
                    
                    <p style="margin-top: 25px; color: #666;">See you soon!<br><strong>The {context['clinic_name']} Team</strong></p>
                </div>
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #999;">
                    <p style="margin: 0;">© 2024 {context['clinic_name']}. All rights reserved.</p>
                </div>
            </div>
        </body>
    </html>
    """


def _get_cancellation_email_html(context):
    """Generate HTML for appointment cancellation email"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">✕ Appointment Cancelled</h1>
                </div>
                <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hello <strong>{context['first_name']}</strong>,</p>
                    <p>Your appointment has been cancelled. Here are the details:</p>
                    
                    <div style="background-color: #f8d7da; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 5px;">
                        <p><strong>📅 Original Date:</strong> {context['appointment_date']}</p>
                        <p><strong>🕐 Original Time:</strong> {context['appointment_time']}</p>
                        <p><strong>💆 Service:</strong> {context['service_name']}</p>
                    </div>
                    
                    <p>If you would like to reschedule, you can book a new appointment on our website or contact us directly.</p>
                    
                    <p style="margin-top: 25px; color: #666;">We look forward to serving you soon!<br><strong>The {context['clinic_name']} Team</strong></p>
                </div>
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #999;">
                    <p style="margin: 0;">© 2024 {context['clinic_name']}. All rights reserved.</p>
                </div>
            </div>
        </body>
    </html>
    """


def _get_rescheduled_email_html(context):
    """Generate HTML for appointment rescheduled email"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">📋 Appointment Rescheduled</h1>
                </div>
                <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hi <strong>{context['first_name']}</strong>,</p>
                    <p>Your appointment has been rescheduled to a new date and time:</p>
                    
                    <div style="background-color: #d4edda; padding: 20px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 5px;">
                        <p><strong>📅 New Date:</strong> {context['appointment_date']}</p>
                        <p><strong>🕐 New Time:</strong> {context['appointment_time']}</p>
                        <p><strong>💆 Service:</strong> {context['service_name']}</p>
                        <p><strong>👨‍⚕️ Attendant:</strong> {context['attendant_name']}</p>
                    </div>
                    
                    <p>Please confirm your attendance or let us know if you need to make further adjustments.</p>
                    
                    <p style="margin-top: 25px; color: #666;">Thank you for your flexibility!<br><strong>The {context['clinic_name']} Team</strong></p>
                </div>
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #999;">
                    <p style="margin: 0;">© 2024 {context['clinic_name']}. All rights reserved.</p>
                </div>
            </div>
        </body>
    </html>
    """


def _get_reassignment_email_html(context):
    """Generate HTML for attendant reassignment email"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">👤 Attendant Changed</h1>
                </div>
                <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hello <strong>{context['first_name']}</strong>,</p>
                    <p>Your appointment attendant has been changed:</p>
                    
                    <div style="background-color: #e8f4f8; padding: 20px; border-left: 4px solid #17a2b8; margin: 20px 0; border-radius: 5px;">
                        <p><strong>📅 Date:</strong> {context['appointment_date']}</p>
                        <p><strong>🕐 Time:</strong> {context['appointment_time']}</p>
                        <p><strong>💆 Service:</strong> {context['service_name']}</p>
                        <p><strong style="color: #28a745;">👨‍⚕️ New Attendant:</strong> {context['attendant_name']}</p>
                    </div>
                    
                    <p>Your new attendant is highly qualified and will provide excellent service. If you have any concerns, please let us know.</p>
                    
                    <p style="margin-top: 25px; color: #666;">See you soon!<br><strong>The {context['clinic_name']} Team</strong></p>
                </div>
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #999;">
                    <p style="margin: 0;">© 2024 {context['clinic_name']}. All rights reserved.</p>
                </div>
            </div>
        </body>
    </html>
    """


def _strip_html_tags(html_text):
    """Strip HTML tags from text for plain text email fallback"""
    import re
    clean_text = re.compile('<.*?>')
    return re.sub(clean_text, '', html_text)
