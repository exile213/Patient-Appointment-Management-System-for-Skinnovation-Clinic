"""
AUTH-NEG-001: Invalid credentials error
Test Scenario: Verify error message is displayed for invalid credentials
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_auth_neg_001_invalid_credentials_error(page: Page):
    """AUTH-NEG-001: Invalid credentials error"""
    # Step 1: Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")

    # Step 2: Click "Login as Patient" link
    page.click("a[href*='/accounts/login/patient/'], a[href*='/login/patient/']")
    page.wait_for_load_state("networkidle")
    
    # Step 3: Enter invalid username
    page.fill('input[name="username"], input#username', "invalid.user")
    
    # Step 4: Enter invalid password
    page.fill('input[name="password"], input#password', "WrongPass123!")
    
    # Step 5: Click "Login" button
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Step 6: Verify error message is displayed
    error_selectors = [
        ".error",
        ".alert",
        ".message",
        "[class*='error']",
        "[class*='alert']",
        "text=Invalid",
        "text=incorrect",
        "text=wrong",
        "text=error",
    ]
    
    error_displayed = False
    for selector in error_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                error_displayed = True
                break
        except:
            continue
    
    assert error_displayed, "Error message should be displayed"
    
    # Step 7: Verify user remains on login page
    assert "/login" in page.url.lower() or "/accounts/login" in page.url.lower()
    
    # Step 8: Verify no redirect occurs
    # Should still be on login page
    assert page.url == f"{BASE_URL}/accounts/login/" or page.url == f"{BASE_URL}/login/patient/" or "/login" in page.url.lower()
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-NEG-001-after.png")

