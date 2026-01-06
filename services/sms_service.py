import requests
import json
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

class SkySMSService:
    """
    SkySMS API Service for sending SMS notifications
    Documentation: https://skysms.skyio.site/
    """
    
    def __init__(self):
        raw_key = getattr(settings, 'SKYSMS_API_KEY', None)
        self.api_key = raw_key.strip() if isinstance(raw_key, str) else raw_key
        self.base_url = "https://skysms.skyio.site"
        
        if not self.api_key:
            raise ImproperlyConfigured("SKYSMS_API_KEY not found in settings")
    
    def send_sms(self, phone, message, sender_id="BEAUTY"):
        """
        Send SMS using SkySMS API
        
        Args:
            phone (str): Recipient's phone number (format: +639xxxxxxxxx or 09xxxxxxxxx)
            message (str): SMS message content (max 160 characters)
            sender_id (str): Sender ID (not used by SkySMS, kept for compatibility)
        
        Returns:
            dict: API response
        """
        # Format phone number to international format
        formatted_number = self._format_phone(phone)
        
        # Ensure message is not empty
        safe_message = message or "[missing message body]"
        
        # Prepare API request using SkySMS API format
        url = f"{self.base_url}/api/v1/sms/send"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        # SkySMS payload format - transactional messaging
        payload = {
            'phone_number': formatted_number,
            'message': safe_message,
            'use_subscription': False
        }
        
        try:
            # Debug logging
            print(f"SMS API Debug - URL: {url}")
            masked_key = f"{str(self.api_key)[:4]}***len:{len(str(self.api_key))}" if self.api_key else "<missing>"
            print(f"SMS API Debug - Headers: {headers}")
            print(f"SMS API Debug - Payload: {payload}")
            print(f"SMS API Debug - API Key (masked): {masked_key}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"SMS API Debug - Response Status: {response.status_code}")
            print(f"SMS API Debug - Response Text: {response.text}")
            
            # Check if response is successful (SkySMS returns 201 for queued messages)
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    print(f"SMS API Debug - Response Data: {response_data}")
                    
                    # Check if the API response indicates success (SkySMS uses "success" field)
                    if response_data.get('success') is True:
                        return {
                            'success': True,
                            'data': response_data,
                            'message': response_data.get('message', 'SMS queued successfully')
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"API Error: {response_data.get('message', 'Unknown error')}",
                            'message': f"Failed to send SMS: {response_data.get('message', 'Unknown error')}"
                        }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Invalid JSON response',
                        'message': 'Failed to send SMS: Invalid response from server'
                    }
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            print(f"SMS API Debug - Request Exception: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to send SMS: {str(e)}'
            }
        except Exception as e:
            print(f"SMS API Debug - General Exception: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Unexpected error occurred: {str(e)}'
            }
    
    def _format_phone(self, phone):
        """
        Format phone number for SkySMS API
        Validates Philippine phone numbers (11 digits starting with 09)
        Returns format: +639xxxxxxxxx (with + prefix)
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Validate Philippine phone number format
        if len(digits) == 11 and digits.startswith('09'):
            # Valid Philippine format (09xxxxxxxxx) -> +639xxxxxxxxx
            return f"+63{digits[1:]}"
        elif len(digits) == 10 and digits.startswith('9'):
            # Philippine format without 0 (9xxxxxxxxx) -> +639xxxxxxxxx
            return f"+63{digits}"
        elif len(digits) == 12 and digits.startswith('639'):
            # Format without + (639xxxxxxxxx) -> +639xxxxxxxxx
            return f"+{digits}"
        elif len(digits) == 13 and digits.startswith('639'):
            # International format with + already included
            return f"+{digits}"
        else:
            # Invalid format - raise an error
            raise ValueError(f"Invalid Philippine phone number format: {phone}. Expected 11 digits starting with 09 (e.g., 09123456789)")
    
    def send_appointment_scheduled(self, appointment, template_name=None):
        """
        Send appointment scheduled SMS using template
        """
        from .template_service import template_service
        return template_service.send_appointment_scheduled(appointment, template_name)
    
    def send_appointment_confirmation(self, appointment, template_name=None):
        """
        Send appointment confirmation SMS using template
        """
        from .template_service import template_service
        return template_service.send_appointment_confirmation(appointment, template_name)
    
    def send_appointment_reminder(self, appointment, template_name=None):
        """
        Send appointment reminder SMS using template
        """
        from .template_service import template_service
        return template_service.send_appointment_reminder(appointment, template_name)
    
    def send_cancellation_notification(self, appointment, reason="", template_name=None):
        """
        Send appointment cancellation notification using template
        """
        from .template_service import template_service
        return template_service.send_cancellation_notification(appointment, reason, template_name)
    
    def send_attendant_reassignment(self, appointment, previous_attendant=None, template_name=None):
        """
        Send attendant reassignment notification using template
        """
        from .template_service import template_service
        return template_service.send_attendant_reassignment(appointment, previous_attendant, template_name)
    
    def send_package_confirmation(self, package_booking, template_name=None):
        """
        Send package booking confirmation SMS using template
        """
        from .template_service import template_service
        return template_service.send_package_confirmation(package_booking, template_name)

    def send_two_day_reminder(self, appointment, template_name=None):
        """
        Send 2-day pre-appointment reminder SMS asking patient to confirm attendance
        """
        from .template_service import template_service
        return template_service.send_two_day_reminder(appointment, template_name)

    def test_api_connection(self):
        """
        Test the API connection with a simple request
        """
        try:
            # Test with a dummy phone number to check API connectivity
            test_payload = {
                'phone_number': '+639123456789',  # Dummy number
                'message': 'API Test',
                'use_subscription': False
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/sms/send",
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': self.api_key
                },
                json=test_payload,
                timeout=10
            )
            
            masked_key = f"{str(self.api_key)[:4]}***len:{len(str(self.api_key))}" if self.api_key else "<missing>"
            print(f"API Test - Status: {response.status_code}")
            print(f"API Test - Response: {response.text}")
            print(f"API Test - API Key (masked): {masked_key}")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"API Test - Error: {str(e)}")
            return False

# Global SMS service instance
sms_service = SkySMSService()
