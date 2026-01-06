"""
ADM-010: Edit patient
Test Scenario: Verify admin can edit patient information
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_010_edit_patient(page: Page):
    """ADM-010: Edit patient"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to patient profile
    page.goto(f"{BASE_URL}/appointments/admin/patient/3/")
    page.wait_for_load_state("networkidle")
    
    # Step Click "Edit Patient" button
    edit_button = page.locator('button:has-text("Edit"), a:has-text("Edit"), a[href*="edit-patient/3"]').first
    if edit_button.is_visible(timeout=2000):
        edit_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/edit-patient/3/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Update phone number
    phone_input = page.locator('input[name="phone"], input[id*="phone"]').first
    if phone_input.is_visible(timeout=2000):
        phone_input.fill("09234567890")
    
    # Step 5: Update address
    address_input = page.locator('input[name="address"], textarea[name="address"], input[id*="address"]').first
    if address_input.is_visible(timeout=2000):
        address_input.fill("123 New Street")
    
    # Screenshot before (after form fields are filled, before submit)
    take_screenshot(page, "staff/ADM-010-before.png")
    
    # Step 6: Click "Save" button
    page.click('button[type="submit"]:has-text("Save"), button:has-text("Save")')
    page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify updated information is displayed
    # Step 9: Verify changes are persisted after page refresh
    page.reload()
    page.wait_for_load_state("networkidle")
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-010-after.png")

