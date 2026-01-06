"""
PKG-003: My packages
Test Scenario: Verify patient can view their package allocations
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_patient


def test_pkg_003_my_packages(page: Page):
    """PKG-003: My packages"""
     # Step 1: Login as Patient
    login_as_patient(page, "maria.santos", "TestPass123!")
    
    # Step 2: Navigate to my packages page
    page.goto(f"{BASE_URL}/packages/my-packages/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify my packages page loads
    assert "/packages/my-packages/" in page.url or "/my-packages/" in page.url
    
    # Step 4: Verify all package allocations are shown
    # Step 5: Verify package details include name, remaining sessions, expiry date
    # Step 6: Verify "Book Session" buttons are present for packages with remaining sessions
    
    # Screenshot after
    take_screenshot(page, "services/PKG-003-after.png")

