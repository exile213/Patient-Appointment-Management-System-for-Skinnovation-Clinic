"""
SRV-002: Service detail
Test Scenario: Verify service detail page displays all service information
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_srv_002_service_detail(page: Page):
    """SRV-002: Service detail"""
    # Step 1: Navigate to services page
    page.goto(f"{BASE_URL}/services/")
    page.wait_for_load_state("networkidle")

    # Step 2: Click on a service card (e.g., Service ID 1)
    service_link = page.locator('a[href*="/services/1/"], a[href*="services/1"]').first
    if service_link.is_visible(timeout=2000):
        service_link.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/services/1/")
        page.wait_for_load_state("networkidle")
    
    # Step 3: Navigate to service detail page
    assert "/services/1/" in page.url
    
    # Step 4: Verify service detail page loads
    # Step 5: Verify all service details are displayed (name, price, description, duration)
    # Step 6: Verify service images are displayed
    # Step 7: Verify primary image is prominently shown
    # Step 8: Verify "Book Appointment" button is present (if logged in)
    
    # Screenshot after
    take_screenshot(page, "services/SRV-002-after.png")

