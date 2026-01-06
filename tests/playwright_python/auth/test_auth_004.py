"""
AUTH-004: Owner login success
Test Scenario: Verify owner can login successfully and redirect to owner dashboard
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_auth_004_owner_login_success(page: Page):
    """AUTH-004: Owner login success"""
    # Step 1: Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")
    
    # Step 2: Click "Login as Owner" link
    page.click("a[href*='/accounts/login/owner/'], a[href*='/login/owner/']")
    page.wait_for_load_state("networkidle")
    
    # Step 3: Enter username
    page.fill('input[name="username"], input#username', "clinic.owner")
    
    # Step 4: Enter password
    page.fill('input[name="password"], input#password', "OwnerPass123!")
    
    # Screenshot before (after form fields are filled, before submit)
    take_screenshot(page, "auth/AUTH-004-before.png")
    
    # Step 5: Click "Login" button
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Step 6: Verify redirect to /owner/
    page.wait_for_url(f"{BASE_URL}/owner/**", timeout=10000)
    assert "/owner/" in page.url
    
    # Step 7: Verify owner dashboard loads
    # Check for dashboard elements
    dashboard_indicators = [
        "text=Owner",
        "text=Dashboard",
        "text=Analytics",
    ]
    
    dashboard_loaded = False
    for indicator in dashboard_indicators:
        try:
            if page.locator(indicator).first.is_visible(timeout=2000):
                dashboard_loaded = True
                break
        except:
            continue
    
    assert dashboard_loaded, "Owner dashboard should load"
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-004-after.png")

