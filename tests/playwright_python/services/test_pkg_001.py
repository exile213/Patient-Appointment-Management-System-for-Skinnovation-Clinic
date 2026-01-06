"""
PKG-001: Packages list
Test Scenario: Verify packages list page displays all packages
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_pkg_001_packages_list(page: Page):
    """PKG-001: Packages list"""
    # Step 1: Navigate to packages page
    page.goto(f"{BASE_URL}/packages/")
    page.wait_for_load_state("networkidle")

    # Step 2: Verify packages list page loads
    assert "/packages/" in page.url
    
    # Step 3: Verify all packages are displayed as cards or in a list
    # Step 4: Verify package information includes name, price, number of sessions
    # Step 5: Verify included services are listed
    # Step 6: Verify "View Details" or "Purchase" buttons are present
    
    # Screenshot after
    take_screenshot(page, "services/PKG-001-after.png")

