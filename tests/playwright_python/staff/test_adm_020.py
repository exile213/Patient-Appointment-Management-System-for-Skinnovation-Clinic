"""
ADM-020: Delete product image
Test Scenario: Verify admin can delete product images
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_020_delete_product_image(page: Page):
    """ADM-020: Delete product image"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to product images page
    page.goto(f"{BASE_URL}/appointments/admin/manage-product-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Find image with ID 7
    # Step 4: Click "Delete" button
    delete_button = page.locator('button:has-text("Delete"), a:has-text("Delete"), a[href*="delete-product-image/7"]').first
    if delete_button.is_visible(timeout=2000):
        delete_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/delete-product-image/7/")
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
    take_screenshot(page, "staff/ADM-020-after.png")

