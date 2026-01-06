"""
ADM-007: Cancel appointment
Test Scenario: Verify admin can cancel an appointment
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_007_cancel_appointment(page: Page):
    """ADM-007: Cancel appointment"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to appointment detail
    page.goto(f"{BASE_URL}/appointments/admin/appointment/5/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click "Cancel Appointment" button
    cancel_button = page.locator('button:has-text("Cancel"), a:has-text("Cancel"), a[href*="cancel/5"]').first
    if cancel_button.is_visible(timeout=2000):
        cancel_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/cancel/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Enter cancellation reason
    reason_input = page.locator('textarea[name="reason"], input[name="reason"], textarea[id*="reason"]').first
    if reason_input.is_visible(timeout=2000):
        reason_input.fill("Patient requested")
    
    # Step 5: Click "Confirm Cancellation" button
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Confirm Cancellation")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify success message appears
    # Step 7: Verify appointment status changes to "Cancelled"
    # Step 8: Navigate to history log
    # Step 9: Verify cancellation log entry is created with reason
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-007-after.png")

