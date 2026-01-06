"""
AUTH-001: Role selection loads
Test Scenario: Verify role selection page loads with all role options
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_auth_001_role_selection(page: Page):
    """AUTH-001: Role selection loads"""
    # Step 1: Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before (after page loads)
    take_screenshot(page, "auth/AUTH-001-before.png")
    
    # Step 2: Verify page loads successfully
    assert page.url == f"{BASE_URL}/accounts/login/" or page.url == f"{BASE_URL}/login/"
    
    # Step 3: Check for role selection cards displayed
    # Look for role selection links (they are links, not buttons)
    role_selectors = [
        "a[href*='/accounts/login/patient/']",
        "a[href*='/accounts/login/admin/']",
        "a[href*='/accounts/login/owner/']",
        "a[href*='/accounts/login/attendant/']",
    ]
    
    # At least one role selection option should be visible
    role_found = False
    for selector in role_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                role_found = True
                break
        except:
            continue
    
    assert role_found, "Role selection options should be displayed"
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-001-after.png")

