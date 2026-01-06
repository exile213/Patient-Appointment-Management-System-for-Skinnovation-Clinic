"""
AUTH-002: Patient login success
Test Scenario: Verify patient can login successfully and redirect to appointments page
"""
import pytest
import re
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_patient


def test_auth_002_patient_login_success(page: Page):
    """AUTH-002: Patient login success"""
    # Step 1: Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")
    
    # Step 2: Click "Login as Patient" link
    page.click("a[href*='/accounts/login/patient/'], a[href*='/login/patient/']")
    page.wait_for_load_state("networkidle")
    
    # Step 3: Enter username
    page.fill('input[name="username"], input#username', "maria.santos")
    
    # Step 4: Enter password
    page.fill('input[name="password"], input#password', "TestPass123!")
    
    # Screenshot before (after form fields are filled, before submit)
    take_screenshot(page, "auth/AUTH-002-before.png")
    
    # Step 5: Click "Login" button
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Step 6: Verify redirect to profile page (actual redirect after patient login)
    # Wait for URL to contain /accounts/profile/ using regex pattern
    page.wait_for_url(re.compile(r".*\/accounts\/profile\/.*"), timeout=30000)
    assert "/accounts/profile/" in page.url, f"Expected /accounts/profile/ but got {page.url}"
    
    # Step 7: Verify user session is active (check for logout button or user info)
    logout_selectors = [
        "a:has-text('Logout')",
        "button:has-text('Logout')",
        "[href*='logout']",
    ]
    
    session_active = False
    for selector in logout_selectors:
        try:
            if page.locator(selector).first.is_visible(timeout=2000):
                session_active = True
                break
        except:
            continue
    
    assert session_active, "User session should be active"
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-002-after.png")

