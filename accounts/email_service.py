import mailtrap as mt
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse


class MailtrapEmailService:
    """Email service using Mailtrap API for sending emails"""
    
    def __init__(self):
        self.api_token = settings.MAILTRAP_API_TOKEN
        self.client = mt.MailtrapClient(token=self.api_token)
    
    def send_password_reset_email(self, user, reset_url):
        """Send password reset email using Mailtrap API"""
        
        # Render the email template
        html_content = render_to_string('accounts/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'Skinovation Beauty Clinic',
        })
        
        # Create the email
        mail = mt.Mail(
            sender=mt.Address(
                email="noreply@skinovation.com", 
                name="Skinovation Beauty Clinic"
            ),
            to=[mt.Address(email=user.email, name=user.get_full_name())],
            subject="Password Reset - Skinovation Beauty Clinic",
            html=html_content,
            text=f"Hello {user.first_name},\n\n"
                 f"We received a request to reset your password for your Skinovation Beauty Clinic account.\n\n"
                 f"Click the link below to reset your password:\n{reset_url}\n\n"
                 f"This link will expire in 1 hour for your security.\n\n"
                 f"If you didn't request this password reset, please ignore this email.\n\n"
                 f"Best regards,\nSkinovation Beauty Clinic Team",
            category="Password Reset",
        )
        
        try:
            response = self.client.send(mail)
            print(f"Mailtrap API Response: {response}")  # Debug logging
            return {
                'success': True,
                'response': response,
                'message': 'Password reset email sent successfully!'
            }
        except Exception as e:
            print(f"Mailtrap API Error: {str(e)}")  # Debug logging
            print(f"Error type: {type(e).__name__}")  # Debug logging
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to send password reset email: {str(e)}'
            }
    
    def send_test_email(self, to_email, to_name="Test User"):
        """Send a test email to verify Mailtrap setup"""
        
        mail = mt.Mail(
            sender=mt.Address(
                email="noreply@skinovation.com", 
                name="Skinovation Beauty Clinic"
            ),
            to=[mt.Address(email=to_email, name=to_name)],
            subject="Test Email - Skinovation Beauty Clinic",
            text="This is a test email from Skinovation Beauty Clinic to verify Mailtrap integration is working correctly!",
            html="<h2>Test Email</h2><p>This is a test email from <strong>Skinovation Beauty Clinic</strong> to verify Mailtrap integration is working correctly!</p>",
            category="Test Email",
        )
        
        try:
            response = self.client.send(mail)
            return {
                'success': True,
                'response': response,
                'message': 'Test email sent successfully!'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send test email'
            }
