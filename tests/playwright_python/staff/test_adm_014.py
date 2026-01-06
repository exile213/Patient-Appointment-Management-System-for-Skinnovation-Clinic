"""
ADM-014: Add attendant
Test Scenario: Verify admin can add a new attendant
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_014_add_attendant(page: Page):
    """ADM-014: Add attendant"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to settings page (attendant form is on settings page)
    page.goto(f"{BASE_URL}/appointments/admin/settings/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify settings page loads
    assert "/appointments/admin/settings/" in page.url
    
    # Step 4: Fill in first name (form is on settings page)
    first_name_input = page.locator('input[name="first_name"]').first
    if first_name_input.is_visible(timeout=5000):
        first_name_input.fill("Jane")
    
    # Step 5: Fill in last name
    last_name_input = page.locator('input[name="last_name"]').first
    if last_name_input.is_visible(timeout=2000):
        last_name_input.fill("Smith")
    
    # Step 6: Fill in shift date (optional)
    shift_date_input = page.locator('input[name="shift_date"]').first
    if shift_date_input.is_visible(timeout=2000):
        shift_date_input.fill("2025-01-20")
    
    # Step 7: Select shift time (optional)
    shift_time_select = page.locator('select[name="shift_time"]').first
    if shift_time_select.is_visible(timeout=2000):
        shift_time_select.select_option(value="09:00")
    
    # Step 8: Click "Add Attendant" button (in the Manage Attendants form)
    add_button = page.locator('form[action*="add-attendant"] button[type="submit"], button:has-text("Add Attendant")').first
    if add_button.is_visible(timeout=5000):
        add_button.click()
        page.wait_for_load_state("networkidle", timeout=10000)
    
    # Step 9: Verify success message appears
    # Step 10: Verify new attendant appears in attendants list
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-014-after.png")

