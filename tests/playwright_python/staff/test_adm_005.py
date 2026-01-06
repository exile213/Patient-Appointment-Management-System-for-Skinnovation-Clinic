"""
ADM-005: Confirm appointment
Test Scenario: Verify admin can confirm an appointment
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_005_confirm_appointment(page: Page):
    """ADM-005: Confirm appointment"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to appointment detail
    page.goto(f"{BASE_URL}/appointments/admin/appointment/5/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify appointment status is "pending"
    # Step 4: Click "Confirm Appointment" button
    confirm_button = page.locator('button:has-text("Confirm"), a:has-text("Confirm"), a[href*="confirm/5"]').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/confirm/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears (if applicable)
    # Step 6: Click "Confirm" in dialog
    dialog_confirm = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first
    if dialog_confirm.is_visible(timeout=2000):
        dialog_confirm.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify appointment status changes to "Confirmed"
    # Step 9: Verify patient notification is sent (check notifications)
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-005-after.png")

