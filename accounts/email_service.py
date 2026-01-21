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
    def send_welcome_email(self, user):
        """Send welcome email to new patient after successful registration"""
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center;">
                        <h1 style="margin: 0; font-size: 28px;">Welcome to Skinnovation Beauty Clinic!</h1>
                    </div>
                    <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                        <p>Hello <strong>{user.first_name}</strong>,</p>
                        <p>Welcome to <strong>Skinnovation Beauty Clinic</strong>! We're thrilled to have you join our community of beauty enthusiasts.</p>
                        
                        <h2 style="color: #667eea; font-size: 18px; margin-top: 25px;">Getting Started:</h2>
                        <ul style="line-height: 1.8;">
                            <li><strong>Complete Your Profile:</strong> Add more details to help us serve you better</li>
                            <li><strong>Browse Our Services:</strong> Explore our range of beauty treatments and packages</li>
                            <li><strong>Book an Appointment:</strong> Schedule your first appointment at your convenience</li>
                            <li><strong>Refer Friends:</strong> Earn rewards when you refer friends to our clinic</li>
                        </ul>
                        
                        <h2 style="color: #667eea; font-size: 18px; margin-top: 25px;">Our Services:</h2>
                        <p>We offer a wide range of beauty treatments including:</p>
                        <ul style="line-height: 1.8;">
                            <li>Skincare Treatments (Facials, Infusion, Whitening)</li>
                            <li>Advanced Treatments (IPL, Laser, Cavitation)</li>
                            <li>Exclusive Packages & Bundles</li>
                        </ul>
                        
                        <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #667eea; margin: 25px 0;">
                            <p style="margin: 0;"><strong>Need Help?</strong> Our customer service team is available to assist you. Simply reply to this email or contact us at the clinic.</p>
                        </div>
                        
                        <p style="margin-top: 25px; color: #666;">Best regards,<br><strong>The Skinnovation Beauty Clinic Team</strong></p>
                    </div>
                    <div style="background-color: #f1f1f1; padding: 15px; text-align: center; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #999;">
                        <p style="margin: 0;">© 2024 Skinnovation Beauty Clinic. All rights reserved.<br>
                        This is an automated welcome email. Please do not reply directly.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Skinnovation Beauty Clinic!
        
        Hello {user.first_name},
        
        Welcome to Skinnovation Beauty Clinic! We're thrilled to have you join our community.
        
        Getting Started:
        - Complete Your Profile: Add more details to help us serve you better
        - Browse Our Services: Explore our range of beauty treatments and packages
        - Book an Appointment: Schedule your first appointment at your convenience
        - Refer Friends: Earn rewards when you refer friends to our clinic
        
        Best regards,
        The Skinnovation Beauty Clinic Team
        """
        
        mail = mt.Mail(
            sender=mt.Address(
                email="noreply@skinovation.com", 
                name="Skinnovation Beauty Clinic"
            ),
            to=[mt.Address(email=user.email, name=user.get_full_name())],
            subject="Welcome to Skinnovation Beauty Clinic!",
            html=html_content,
            text=text_content,
            category="Welcome",
        )
        
        try:
            response = self.client.send(mail)
            print(f"Welcome Email Response: {response}")
            return {
                'success': True,
                'response': response,
                'message': 'Welcome email sent successfully!'
            }
        except Exception as e:
            print(f"Welcome Email Error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to send welcome email: {str(e)}'
            }