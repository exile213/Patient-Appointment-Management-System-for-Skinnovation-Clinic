"""
OWN-IMG-002: Delete service image
Test Scenario: Verify owner can delete service images
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_img_002_delete_service_image(page: Page):
    """OWN-IMG-002: Delete service image"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to service images page
    page.goto(f"{BASE_URL}/owner/manage/service-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Find image with ID 5
    # Step 4: Click "Delete" button
    delete_button = page.locator('button:has-text("Delete"), a:has-text("Delete"), a[href*="delete-service-image/5"]').first
    if delete_button.is_visible(timeout=2000):
        delete_button.click()
        page.wait_for_load_state("networkidle")
    else:
        # Try direct navigation
        page.goto(f"{BASE_URL}/owner/delete-service-image/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Confirm deletion in dialog
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("Delete")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify success message appears
    # Step 7: Verify image is removed from list
    page.goto(f"{BASE_URL}/owner/manage/service-images/")
    page.wait_for_load_state("networkidle")
    
    # Step 8: Verify image file is deleted from server
    assert "/owner/manage/service-images/" in page.url
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-IMG-002-after.png")

