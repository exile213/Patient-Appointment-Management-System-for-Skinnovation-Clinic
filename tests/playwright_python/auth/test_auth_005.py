"""
AUTH-005: Attendant login success
Test Scenario: Verify attendant can login successfully and redirect to attendant dashboard
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_auth_005_attendant_login_success(page: Page):
    """AUTH-005: Attendant login success"""
    # Step 1: Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")
    
    # Step 2: Click "Login as Attendant" link
    page.click("a[href*='/accounts/login/attendant/'], a[href*='/login/attendant/']")
    page.wait_for_load_state("networkidle")
    
    # Step 3: Enter username
    page.fill('input[name="username"], input#username', "attendant.01")
    
    # Step 4: Enter password
    page.fill('input[name="password"], input#password', "AttendPass123!")
    
    # Screenshot before (after form fields are filled, before submit)
    take_screenshot(page, "auth/AUTH-005-before.png")
    
    # Step 5: Click "Login" button
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Step 6: Verify redirect to /attendant/
    page.wait_for_url(f"{BASE_URL}/attendant/**", timeout=10000)
    assert "/attendant/" in page.url
    
    # Step 7: Verify attendant dashboard loads
    # Check for dashboard elements
    dashboard_indicators = [
        "text=Attendant",
        "text=Dashboard",
        "text=Appointments",
    ]
    
    dashboard_loaded = False
    for indicator in dashboard_indicators:
        try:
            if page.locator(indicator).first.is_visible(timeout=2000):
                dashboard_loaded = True
                break
        except:
            continue
    
    assert dashboard_loaded, "Attendant dashboard should load"
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-005-after.png")

