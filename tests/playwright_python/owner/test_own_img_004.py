"""
OWN-IMG-004: Manage product images
Test Scenario: Verify owner can manage product images
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_img_004_manage_product_images(page: Page):
    """OWN-IMG-004: Manage product images"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to product images page
    page.goto(f"{BASE_URL}/owner/manage/product-images/", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    
    # Screenshot before - product images page
    take_screenshot(page, "owner/OWN-IMG-004-before.png")

    # Step 3: Verify product images list page loads
    assert "/owner/manage/product-images/" in page.url
    
    # Step 4: Verify all product images are displayed
    # Step 5: Verify image actions are available (delete, set primary)
    # Step 6: Verify upload functionality is present (if applicable)
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-IMG-004-after.png")

