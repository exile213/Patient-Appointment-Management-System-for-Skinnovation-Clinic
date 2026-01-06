"""
ADM-019: Manage product images
Test Scenario: Verify admin can manage product images
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_019_manage_product_images(page: Page):
    """ADM-019: Manage product images"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to product images page
    page.goto(f"{BASE_URL}/appointments/admin/manage-product-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify product images list page loads
    assert "/appointments/admin/manage-product-images/" in page.url
    
    # Step 4: Verify all product images are displayed
    # Step 5: Verify image actions are available (delete, set primary, upload)
    # Step 6: Test upload functionality (if available)
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-019-after.png")

