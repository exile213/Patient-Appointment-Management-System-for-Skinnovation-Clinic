"""
AUTH-003: Staff login success
Test Scenario: Verify staff/admin can login successfully and redirect to admin dashboard
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_auth_003_staff_login_success(page: Page):
    """AUTH-003: Staff login success"""
    # Step 1: Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")
    
    # Step 2: Click "Login as Admin" link
    page.click("a[href*='/accounts/login/admin/'], a[href*='/login/admin/']")
    page.wait_for_load_state("networkidle")
    
    # Step 3: Enter username
    page.fill('input[name="username"], input#username', "admin.staff")
    
    # Step 4: Enter password
    page.fill('input[name="password"], input#password', "AdminPass123!")
    
    # Screenshot before (after form fields are filled, before submit)
    take_screenshot(page, "auth/AUTH-003-before.png")
    
    # Step 5: Click "Login" button
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Step 6: Verify redirect to /admin/ (actual redirect after admin login)
    page.wait_for_url(f"{BASE_URL}/admin/**", timeout=10000)
    assert "/admin/" in page.url
    
    # Step 7: Verify admin dashboard loads
    # Check for dashboard elements
    dashboard_indicators = [
        "text=Dashboard",
        "text=Admin",
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
    
    assert dashboard_loaded, "Admin dashboard should load"
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-003-after.png")

