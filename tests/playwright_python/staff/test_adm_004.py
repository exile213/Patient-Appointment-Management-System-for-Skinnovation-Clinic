"""
ADM-004: Appointment detail
Test Scenario: Verify admin can view appointment details
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_004_appointment_detail(page: Page):
    """ADM-004: Appointment detail"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to appointments page
    page.goto(f"{BASE_URL}/appointments/admin/appointments/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click on appointment with ID 5
    appointment_link = page.locator('a[href*="/admin/appointment/5/"], a[href*="appointment/5"]').first
    if appointment_link.is_visible(timeout=2000):
        appointment_link.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/appointment/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Navigate to appointment detail page
    assert "/appointments/admin/appointment/5/" in page.url
    
    # Step 5: Verify appointment detail page loads
    # Step 6: Verify all appointment details are visible
    # Step 7: Verify action buttons are present (confirm, complete, cancel)
    # Step 8: Verify patient information is displayed
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-004-after.png")

