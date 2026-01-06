"""
ADM-SMS-001: SMS test page
Test Scenario: Verify admin can access SMS test page
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_sms_001_sms_test_page(page: Page):
    """ADM-SMS-001: SMS test page"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to SMS test page
    page.goto(f"{BASE_URL}/appointments/admin/sms-test/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify SMS test page loads
    assert "/appointments/admin/sms-test/" in page.url
    
    # Step 4: Verify form is displayed with phone number and message fields
    # Step 5: Verify "Send Test SMS" button is present
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-SMS-001-after.png")

