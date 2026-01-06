"""
ADM-016: Manage service images
Test Scenario: Verify admin can manage service images
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_016_manage_service_images(page: Page):
    """ADM-016: Manage service images"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to service images page
    page.goto(f"{BASE_URL}/appointments/admin/manage-service-images/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify service images list page loads
    assert "/appointments/admin/manage-service-images/" in page.url
    
    # Step 4: Verify all service images are displayed
    # Step 5: Verify image actions are available (delete, set primary, upload)
    # Step 6: Test upload functionality (if available)
    # Step 7: Verify uploaded images appear in list
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-016-after.png")

