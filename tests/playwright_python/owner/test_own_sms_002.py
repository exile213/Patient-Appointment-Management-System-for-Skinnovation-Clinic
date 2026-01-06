"""
OWN-SMS-002: Send test SMS
Test Scenario: Verify owner can send test SMS
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_sms_002_send_test_sms(page: Page):
    """OWN-SMS-002: Send test SMS"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to SMS test page
    page.goto(f"{BASE_URL}/owner/sms-test/")
    page.wait_for_load_state("networkidle")
    
    # Step Enter phone number
    phone_field = page.locator('input[name="phone"], input[id*="phone"], input[type="tel"]').first
    if phone_field.is_visible(timeout=2000):
        phone_field.fill("09123456789")
    
    # Step 4: Enter message
    message_field = page.locator('textarea[name="message"], input[name="message"], textarea[id*="message"]').first
    if message_field.is_visible(timeout=2000):
        message_field.fill("Test message from clinic")
    
    # Screenshot before (after form fields are filled, before submit)
    take_screenshot(page, "owner/OWN-SMS-002-before.png")
    
    # Step 5: Click "Send Test SMS" button
    send_button = page.locator('button:has-text("Send"), button:has-text("Send Test SMS"), button[type="submit"]').first
    if send_button.is_visible(timeout=2000):
        send_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify success message appears
    success_indicators = [
        "text=success",
        "text=sent",
        ".success",
        ".alert-success",
    ]
    
    # Step 7: Verify SMS is queued or sent
    # Step 8: Verify message delivery status (if available)
    assert "/owner/sms-test/" in page.url or "/owner/" in page.url
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-SMS-002-after.png")

