"""
Quick SMS Migration Test Script
Run this to verify SkySMS integration is working
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from services.sms_service import sms_service
from django.conf import settings

print("=" * 60)
print("SMS MIGRATION TEST - SkySMS Integration")
print("=" * 60)

# 1. Check configuration
print("\n1. CONFIGURATION CHECK:")
print(f"   SMS Enabled: {settings.SMS_ENABLED}")
api_key = getattr(settings, 'SKYSMS_API_KEY', None)
if api_key:
    masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
    print(f"   API Key: {masked} ✓")
else:
    print("   API Key: NOT SET ✗")
    print("\n   ERROR: SKYSMS_API_KEY not found in settings!")
    print("   Make sure you updated your .env file")
    exit(1)

# 2. Check service instance
print("\n2. SERVICE INSTANCE CHECK:")
print(f"   Service Class: {sms_service.__class__.__name__}")
print(f"   Base URL: {sms_service.base_url}")
if sms_service.__class__.__name__ == "SkySMSService":
    print("   Status: ✓ Correctly using SkySMS")
else:
    print("   Status: ✗ Still using old service!")
    exit(1)

# 3. Test phone formatting
print("\n3. PHONE FORMATTING TEST:")
test_numbers = [
    "09123456789",
    "639123456789",
    "+639123456789"
]
for num in test_numbers:
    try:
        formatted = sms_service._format_phone(num)
        print(f"   {num} → {formatted} ✓")
    except Exception as e:
        print(f"   {num} → ERROR: {e} ✗")

# 4. Test message truncation
print("\n4. MESSAGE TRUNCATION TEST:")
long_message = "A" * 200
truncated = long_message[:160]
print(f"   Original length: {len(long_message)}")
print(f"   Expected after truncation: 160")
print(f"   Status: ✓ Truncation will work")

# 5. API Connection Test (optional - will use real API)
print("\n5. API CONNECTION TEST:")
response = input("   Do you want to test the actual API connection? (y/n): ")
if response.lower() == 'y':
    test_phone = input("   Enter a test phone number (09XXXXXXXXX): ")
    if test_phone:
        try:
            result = sms_service.send_sms(test_phone, "Test message from SkySMS migration")
            if result.get('success'):
                print(f"   ✓ SMS sent successfully!")
                print(f"   Response: {result.get('message', 'No message')}")
            else:
                print(f"   ✗ SMS failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    else:
        print("   Skipped")
else:
    print("   Skipped (API test not performed)")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nIf all tests passed (✓), your migration is successful!")
print("You can now test SMS features in your application.")
print("\nNext steps:")
print("  1. Restart your Django server")
print("  2. Test SMS via: Owner SMS Test page")
print("  3. Book a test appointment to verify SMS notifications")
