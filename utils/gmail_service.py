"""
Gmail API Email Service
Unified email service using Gmail API with OAuth2 for all email sending needs.
Replaces both Mailjet and Mailtrap implementations.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


class GmailAPIService:
    """Email service using Gmail API with OAuth2 for sending emails"""
    
    def __init__(self):
        """Initialize Gmail API service with OAuth2 credentials"""
        try:
            # Get OAuth2 credentials from settings
            self.client_id = settings.GMAIL_CLIENT_ID
            self.client_secret = settings.GMAIL_CLIENT_SECRET
            self.refresh_token = settings.GMAIL_REFRESH_TOKEN
            self.sender_email = settings.GMAIL_SENDER_EMAIL
            
            # Create credentials object
            self.credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=['https://www.googleapis.com/auth/gmail.send']
            )
            
            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("[GMAIL API] Service initialized successfully")
            
        except AttributeError as e:
            raise ValueError(
                f"Gmail API credentials not configured: {str(e)}. "
                "Please set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, "
                "GMAIL_REFRESH_TOKEN, and GMAIL_SENDER_EMAIL in your environment variables."
            )
        except Exception as e:
            logger.error(f"[GMAIL API] Failed to initialize service: {str(e)}")
            raise
    
    def create_message(self, to_email, subject, html_content, text_content):
        """
        Create a MIME message for Gmail API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email body
            text_content: Plain text version of email body
            
        Returns:
            dict: Message object ready to send via Gmail API
        """
        # Create multipart message
        message = MIMEMultipart('alternative')
        message['To'] = to_email
        message['From'] = f"Skinnovation Beauty Clinic <{self.sender_email}>"
        message['Subject'] = subject
        
        # Attach plain text and HTML parts
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        message.attach(text_part)
        message.attach(html_part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}
    
    def send_email(self, subject, to_email, html_content, text_content, category=None):
        """
        Send an email using Gmail API
        
        Args:
            subject: Email subject line
            to_email: Recipient email address
            html_content: HTML version of the email
            text_content: Plain text version of the email
            category: Optional category for logging purposes
            
        Returns:
            dict: Result with 'success' boolean and 'message' string
        """
        try:
            logger.info(f"[GMAIL API] Sending {category or 'email'} to {to_email}")
            
            # Create message
            message = self.create_message(to_email, subject, html_content, text_content)
            
            # Send message
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            logger.info(f"[GMAIL API] Successfully sent {category or 'email'} to {to_email}. Message ID: {sent_message['id']}")
            return {
                'success': True,
                'message_id': sent_message['id'],
                'message': f'{category or "Email"} sent successfully!'
            }
            
        except HttpError as e:
            error_msg = f"Gmail API HTTP Error: {str(e)}"
            logger.error(f"[GMAIL API] {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to send {category or 'email'}: {str(e)}"
            }
        except Exception as e:
            error_msg = f"Failed to send {category or 'email'}: {str(e)}"
            logger.error(f"[GMAIL API] {error_msg}")
            logger.exception(e)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def send_welcome_email(self, user):
        """
        Send welcome email to new patient after successful registration
        
        Args:
            user: User object for the new patient
            
        Returns:
            dict: Result with 'success' boolean and 'message' string
        """
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
                            <li>Exclusive Packages &amp; Bundles</li>
                        </ul>
                        
                        <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #667eea; margin: 25px 0;">
                            <p style="margin: 0;"><strong>Need Help?</strong> Our customer service team is available to assist you. Simply reply to this email or contact us at the clinic.</p>
                        </div>
                        
                        <p style="margin-top: 25px; color: #666;">Best regards,<br><strong>The Skinnovation Beauty Clinic Team</strong></p>
                    </div>
                    <div style="background-color: #f1f1f1; padding: 15px; text-align: center; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #999;">
                        <p style="margin: 0;">© 2024 Skinnovation Beauty Clinic. All rights reserved.<br>
                        This is an automated welcome email.</p>
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
        
        return self.send_email(
            subject="Welcome to Skinnovation Beauty Clinic!",
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            category="Welcome"
        )
    
    def send_password_reset_email(self, user, reset_url):
        """
        Send password reset email using Gmail API
        
        Args:
            user: User object requesting password reset
            reset_url: URL for password reset
            
        Returns:
            dict: Result with 'success' boolean and 'message' string
        """
        # Render the email template
        html_content = render_to_string('accounts/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'Skinnovation Beauty Clinic',
        })
        
        text_content = f"""
        Hello {user.first_name},
        
        We received a request to reset your password for your Skinnovation Beauty Clinic account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour for your security.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        Skinnovation Beauty Clinic Team
        """
        
        return self.send_email(
            subject="Password Reset - Skinnovation Beauty Clinic",
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            category="Password Reset"
        )
    
    def send_test_email(self, to_email):
        """
        Send a test email to verify Gmail API setup
        
        Args:
            to_email: Recipient email address
            
        Returns:
            dict: Result with 'success' boolean and 'message' string
        """
        html_content = "<h2>Test Email</h2><p>This is a test email from <strong>Skinnovation Beauty Clinic</strong> to verify Gmail API integration is working correctly!</p>"
        text_content = "This is a test email from Skinnovation Beauty Clinic to verify Gmail API integration is working correctly!"
        
        return self.send_email(
            subject="Test Email - Skinnovation Beauty Clinic",
            to_email=to_email,
            html_content=html_content,
            text_content=text_content,
            category="Test Email"
        )
