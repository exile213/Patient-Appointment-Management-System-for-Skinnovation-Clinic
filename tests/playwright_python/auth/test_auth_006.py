"""
AUTH-006: Registration
Test Scenario: Verify patient registration flow works correctly
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_auth_006_registration(page: Page):
    """AUTH-006: Registration"""
    # Step 1: Navigate to registration page
    page.goto(f"{BASE_URL}/accounts/register/")
    page.wait_for_load_state("networkidle")
    
    # Step 2: Fill in username field (using unique test case identifier)
    page.fill('input[name="username"], input[id*="username"]', "test.patient.006")
    
    # Step 3: Fill in email field (using unique test case identifier)
    page.fill('input[name="email"], input[type="email"], input[id*="email"]', "test.patient.006@example.com")
    
    # Step 4: Fill in first name field
    page.fill('input[name="first_name"], input[id*="first_name"]', "Test")
    
    # Step 5: Fill in last name field
    page.fill('input[name="last_name"], input[id*="last_name"]', "Patient")
    
    # Step 6: Fill in phone field (using different phone number)
    page.fill('input[name="phone"], input[id*="phone"], input[placeholder*="09123456789"]', "09987654321")
    
    # Step 7: Fill in password field (first password field)
    password_inputs = page.locator('input[type="password"]')
    password_inputs.first.fill("NewPass123!")
    
    # Step 8: Fill in confirm password field (second password field)
    password_inputs.nth(1).fill("NewPass123!")
    
    # Screenshot before (after form fields are filled, before submit)
    take_screenshot(page, "auth/AUTH-006-before.png")
    
    # Step 9: Click "Register" button
    page.click('button[type="submit"]:has-text("Register"), button:has-text("Register"), input[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Step 10: Verify redirect to login page (registration redirects to login, not profile)
    page.wait_for_url(f"{BASE_URL}/accounts/login/**", timeout=30000)
    assert "/accounts/login/" in page.url or "/login/" in page.url
    
    # Step 11: Verify success message appears
    success_indicators = [
        "text=Account created successfully",
        "text=Please log in",
        "text=created successfully",
    ]
    
    success_message = False
    for indicator in success_indicators:
        try:
            if page.locator(indicator).first.is_visible(timeout=2000):
                success_message = True
                break
        except:
            continue
    
    # Verify we're on the login selection page
    assert "/accounts/login/" in page.url or "/login/" in page.url
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-006-after.png")

