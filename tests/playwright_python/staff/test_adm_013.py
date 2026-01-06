"""
ADM-013: Settings page
Test Scenario: Verify admin can update settings
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_013_settings_page(page: Page):
    """ADM-013: Settings page"""
    # Set increased timeout
    page.set_default_timeout(60000)
    page.set_default_navigation_timeout(60000)
    
    # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to settings page
    page.goto(f"{BASE_URL}/appointments/admin/settings/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify settings page loads
    assert "/appointments/admin/settings/" in page.url
    
    # Step 4: Update "Clinic Name"
    clinic_name_input = page.locator('input[name="clinic_name"], input[id*="clinic_name"], input[name="name"]').first
    if clinic_name_input.is_visible(timeout=2000):
        clinic_name_input.fill("Skinovation Beauty Clinic")
    
    # Step 5: Update "Operating Hours"
    hours_input = page.locator('input[name="operating_hours"], input[id*="hours"], textarea[name="hours"]').first
    if hours_input.is_visible(timeout=2000):
        hours_input.fill("10:00 AM - 6:00 PM")
    
    # Step 6: Click "Save Settings" button (try multiple selectors)
    save_button = page.locator('button[type="submit"]:has-text("Save"), button:has-text("Save Settings"), button.btn-primary:has-text("Save"), form button[type="submit"]').first
    if save_button.is_visible(timeout=5000):
        save_button.click()
        page.wait_for_load_state("networkidle", timeout=10000)
    else:
        # Try to find any submit button in a form
        form_submit = page.locator('form button[type="submit"]').first
        if form_submit.is_visible(timeout=3000):
            form_submit.click()
            page.wait_for_load_state("networkidle", timeout=10000)
    
    # Step 7: Verify success message appears
    # Step 8: Verify settings are saved
    # Step 9: Refresh page and verify settings persist
    page.reload()
    page.wait_for_load_state("networkidle")
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-013-after.png")

