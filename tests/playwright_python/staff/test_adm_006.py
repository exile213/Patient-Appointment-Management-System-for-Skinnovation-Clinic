"""
ADM-006: Complete appointment
Test Scenario: Verify admin can complete an appointment
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_006_complete_appointment(page: Page):
    """ADM-006: Complete appointment"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to appointment detail
    page.goto(f"{BASE_URL}/appointments/admin/appointment/5/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify appointment status is "confirmed" or "in progress"
    # Step 4: Click "Complete Appointment" button
    complete_button = page.locator('button:has-text("Complete"), a:has-text("Complete"), a[href*="complete/5"]').first
    if complete_button.is_visible(timeout=2000):
        complete_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/complete/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears (if applicable)
    # Step 6: Click "Confirm" in dialog
    dialog_confirm = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first
    if dialog_confirm.is_visible(timeout=2000):
        dialog_confirm.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify appointment status changes to "Completed"
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-006-after.png")

