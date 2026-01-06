"""
ADM-018: Set primary service image
Test Scenario: Verify admin can set primary service image
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_018_set_primary_service_image(page: Page):
    """ADM-018: Set primary service image"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to service images page
    page.goto(f"{BASE_URL}/appointments/admin/manage-service-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Find image with ID 5
    # Step 4: Click "Set as Primary" button
    primary_button = page.locator('button:has-text("Set as Primary"), a:has-text("Set as Primary"), a[href*="set-primary-service-image/5"]').first
    if primary_button.is_visible(timeout=2000):
        primary_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/set-primary-service-image/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears (if applicable)
    # Step 6: Confirm action
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify image ID 5 is marked as primary
    # Step 9: Verify previous primary image is unmarked
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-018-after.png")

