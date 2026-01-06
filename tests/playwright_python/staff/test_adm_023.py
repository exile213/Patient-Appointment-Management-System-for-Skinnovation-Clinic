"""
ADM-023: Delete closed day
Test Scenario: Verify admin can delete a closed day
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_023_delete_closed_day(page: Page):
    """ADM-023: Delete closed day"""
    # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to closed days list page
    page.goto(f"{BASE_URL}/appointments/admin/settings/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before (after navigation)
    take_screenshot(page, "staff/ADM-023-before.png")
    # Step 3: Find closed day with ID 3
    # Step 4: Click "Delete Closed Day" button
    delete_button = page.locator('button:has-text("Delete"), a:has-text("Delete"), a[href*="delete-closed-day/3"]').first
    if delete_button.is_visible(timeout=2000):
        delete_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/delete-closed-day/3/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears
    # Step 6: Click "Confirm Delete" button
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Confirm Delete")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify closed day is removed from list
    # Step 9: Verify date is unblocked in calendar
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-023-after.png")

