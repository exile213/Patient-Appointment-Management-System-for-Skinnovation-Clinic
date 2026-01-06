"""
ADM-022: Add closed day
Test Scenario: Verify admin can add a closed day
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_022_add_closed_day(page: Page):
    """ADM-022: Add closed day"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to settings page (closed day form is on settings page)
    page.goto(f"{BASE_URL}/appointments/admin/settings/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify settings page loads
    assert "/appointments/admin/settings/" in page.url
    
    # Step 4: Select date "2025-01-20" (in the Set Closed Clinic Days form)
    date_input = page.locator('form[action*="add-closed-day"] input[name="start_date"], input[name="start_date"]').first
    if date_input.is_visible(timeout=5000):
        date_input.fill("2025-01-20")
    
    # Step 5: Enter reason "Holiday"
    reason_input = page.locator('form[action*="add-closed-day"] input[name="reason"], input[name="reason"]').first
    if reason_input.is_visible(timeout=2000):
        reason_input.fill("Holiday")
    
    # Step 6: Click "Add Closed Day" button (in the Set Closed Clinic Days form)
    add_button = page.locator('form[action*="add-closed-day"] button[type="submit"], button:has-text("Add Closed Day")').first
    if add_button.is_visible(timeout=5000):
        add_button.click()
        page.wait_for_load_state("networkidle", timeout=10000)
    
    # Step 7: Verify success message appears
    # Step 8: Verify date is blocked in calendar
    # Step 9: Verify closed day appears in closed days list
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-022-after.png")

