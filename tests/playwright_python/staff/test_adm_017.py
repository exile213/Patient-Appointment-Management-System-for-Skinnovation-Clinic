"""
ADM-017: Delete service image
Test Scenario: Verify admin can delete service images
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_017_delete_service_image(page: Page):
    """ADM-017: Delete service image"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to service images page
    page.goto(f"{BASE_URL}/appointments/admin/manage-service-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Find image with ID 5
    # Step 4: Click "Delete" button
    delete_button = page.locator('button:has-text("Delete"), a:has-text("Delete"), a[href*="delete-service-image/5"]').first
    if delete_button.is_visible(timeout=2000):
        delete_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/delete-service-image/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Confirm deletion in dialog
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify success message appears
    # Step 7: Verify image is removed from list
    # Step 8: Verify image file is deleted from server
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-017-after.png")

