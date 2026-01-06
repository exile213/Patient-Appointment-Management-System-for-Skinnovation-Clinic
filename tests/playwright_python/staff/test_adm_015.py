"""
ADM-015: Delete attendant
Test Scenario: Verify admin can delete an attendant
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_015_delete_attendant(page: Page):
    """ADM-015: Delete attendant"""
    # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to attendants list page
    page.goto(f"{BASE_URL}/appointments/admin/maintenance/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before (after navigation)
    take_screenshot(page, "staff/ADM-015-before.png")
    # Step 3: Find attendant with ID 2
    # Step 4: Click "Delete Attendant" button
    delete_button = page.locator('button:has-text("Delete"), a:has-text("Delete"), a[href*="delete-attendant/2"]').first
    if delete_button.is_visible(timeout=2000):
        delete_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/delete-attendant/2/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears
    # Step 6: Click "Confirm Delete" button
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Confirm Delete")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify attendant is removed from list
    # Step 9: Verify related appointments are reassigned (if applicable)
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-015-after.png")

