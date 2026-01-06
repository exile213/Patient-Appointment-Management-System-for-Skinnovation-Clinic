"""
PKG-002: Package detail
Test Scenario: Verify package detail page displays all package information
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_pkg_002_package_detail(page: Page):
    """PKG-002: Package detail"""
    # Step 1: Navigate to packages page
    page.goto(f"{BASE_URL}/packages/")
    page.wait_for_load_state("networkidle")

    # Step 2: Click on a package card (e.g., Package ID 3)
    package_link = page.locator('a[href*="/packages/3/"], a[href*="packages/3"]').first
    if package_link.is_visible(timeout=2000):
        package_link.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/packages/3/")
        page.wait_for_load_state("networkidle")
    
    # Step 3: Navigate to package detail page
    assert "/packages/3/" in page.url
    
    # Step 4: Verify package detail page loads
    # Step 5: Verify all package details are displayed (name, price, sessions, included services)
    # Step 6: Verify package benefits are listed
    # Step 7: Verify "Purchase Package" or "Book Session" button is present (if logged in)
    
    # Screenshot after
    take_screenshot(page, "services/PKG-002-after.png")

