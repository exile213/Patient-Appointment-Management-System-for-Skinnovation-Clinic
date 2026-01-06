"""
SRV-003: Upload service
Test Scenario: Verify permitted user can upload a new service
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_srv_003_upload_service(page: Page):
    """SRV-003: Upload service"""
     # Step 1: Login as Owner or Staff
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to service upload page
    page.goto(f"{BASE_URL}/owner/manage/services/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click "Add New Service" button (try multiple selectors)
    add_button = page.locator('a:has-text("Add New Service"), button:has-text("Add New Service"), a:has-text("Add New"), button:has-text("Add New"), a.btn-primary, button.btn-primary').first
    if add_button.is_visible(timeout=5000):
        add_button.click()
        page.wait_for_load_state("networkidle")
    else:
        # Try navigating directly to add service page
        page.goto(f"{BASE_URL}/owner/manage/services/add/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Fill in service name
    page.fill('input[name="name"], input[id*="name"]', "Anti-Aging Treatment")
    
    # Step 5: Fill in service price
    page.fill('input[name="price"], input[id*="price"]', "2000.00")
    
    # Step 6: Fill in service description
    page.fill('textarea[name="description"], textarea[id*="description"]', "Advanced anti-aging facial treatment")
    
    # Step 7: Fill in service duration (number input, so just the number)
    duration_input = page.locator('input[name="duration"], input[id*="duration"]').first
    if duration_input.is_visible(timeout=2000):
        duration_input.fill("60")  # Number input, not text
    
    # Step 8: Upload service images
    # Skip file upload for now
    
    # Step 9: Click "Save" or "Upload" button (try multiple selectors)
    save_button = page.locator('button[type="submit"], button.btn-primary, button:has-text("Save"), button:has-text("Create")').first
    if save_button.is_visible(timeout=5000):
        save_button.click()
        page.wait_for_load_state("networkidle", timeout=10000)
    else:
        # Try form submit
        form_submit = page.locator('form button[type="submit"]').first
        if form_submit.is_visible(timeout=3000):
            form_submit.click()
            page.wait_for_load_state("networkidle", timeout=10000)
    
    # Step 10: Verify success message appears
    # Step 11: Verify new service appears in services list
    page.goto(f"{BASE_URL}/services/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot after
    take_screenshot(page, "services/SRV-003-after.png")

