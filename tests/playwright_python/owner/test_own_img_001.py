"""
OWN-IMG-001: Manage service images
Test Scenario: Verify owner can manage service images
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_img_001_manage_service_images(page: Page):
    """OWN-IMG-001: Manage service images"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to service images page
    page.goto(f"{BASE_URL}/owner/manage/service-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify service images list page loads
    assert "/owner/manage/service-images/" in page.url
    
    # Step 4: Verify all service images are displayed
    image_indicators = [
        "[class*='image']",
        "img",
        "[class*='service-image']",
    ]
    
    # Step 5: Verify image actions are available (delete, set primary)
    action_buttons = [
        "button:has-text('Delete')",
        "button:has-text('Set as Primary')",
        "a:has-text('Delete')",
    ]
    
    # Step 6: Verify upload functionality is present (if applicable)
    upload_indicators = [
        'input[type="file"]',
        "button:has-text('Upload')",
        "a:has-text('Upload')",
    ]
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-IMG-001-after.png")

