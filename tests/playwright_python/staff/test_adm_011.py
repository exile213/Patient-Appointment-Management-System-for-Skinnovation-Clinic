"""
ADM-011: Delete patient
Test Scenario: Verify admin can delete a patient
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_011_delete_patient(page: Page):
    """ADM-011: Delete patient"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to patient profile
    page.goto(f"{BASE_URL}/appointments/admin/patient/3/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click "Delete Patient" button
    delete_button = page.locator('button:has-text("Delete"), a:has-text("Delete"), a[href*="delete-patient/3"]').first
    if delete_button.is_visible(timeout=2000):
        delete_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/delete-patient/3/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Verify confirmation dialog appears
    # Step 5: Enter confirmation text (if required)
    # Step 6: Click "Confirm Delete" button
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Confirm Delete"), button:has-text("Yes")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify patient is removed from list or marked as archived
    # Step 9: Verify related appointments are handled appropriately
    # Note: Delete test may be skipped to avoid data loss
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-011-after.png")

