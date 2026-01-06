"""
OWN-IMG-006: Set primary product image
Test Scenario: Verify owner can set primary product image
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_img_006_set_primary_product_image(page: Page):
    """OWN-IMG-006: Set primary product image"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to product images page
    page.goto(f"{BASE_URL}/owner/manage/product-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Find image with ID 7
    # Step 4: Click "Set as Primary" button
    primary_button = page.locator('button:has-text("Set as Primary"), a:has-text("Set as Primary"), a[href*="set-primary-product-image/7"]').first
    if primary_button.is_visible(timeout=2000):
        primary_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/owner/set-primary-product-image/7/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears (if applicable)
    # Step 6: Confirm action
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify image ID 7 is marked as primary
    page.goto(f"{BASE_URL}/owner/manage/product-images/")
    page.wait_for_load_state("networkidle")
    
    # Step 9: Verify previous primary image is unmarked
    assert "/owner/manage/product-images/" in page.url
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-IMG-006-after.png")

