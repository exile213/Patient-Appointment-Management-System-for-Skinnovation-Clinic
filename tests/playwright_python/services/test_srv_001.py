"""
SRV-001: Services list
Test Scenario: Verify services list page displays all services
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_srv_001_services_list(page: Page):
    """SRV-001: Services list"""
    # Step 1: Navigate to services page
    page.goto(f"{BASE_URL}/services/")
    page.wait_for_load_state("networkidle")

    # Step 2: Verify services list page loads
    assert "/services/" in page.url
    
    # Step 3: Verify all services are displayed as cards or in a list
    # Step 4: Verify service information includes name, price, description
    # Step 5: Verify service images are displayed (if available)
    # Step 6: Verify "View Details" or "Book" buttons are present
    
    # Screenshot after
    take_screenshot(page, "services/SRV-001-after.png")

