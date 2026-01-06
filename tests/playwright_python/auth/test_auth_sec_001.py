"""
AUTH-SEC-001: Cross-role access denied
Test Scenario: Verify patient cannot access admin or owner pages
"""
import pytest
import re
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_patient


def test_auth_sec_001_cross_role_access_denied(page: Page):
    """AUTH-SEC-001: Cross-role access denied"""
     # Step 1: Login as Patient
    login_as_patient(page, "maria.santos", "TestPass123!")
    
    

    # Screenshot before (after login completes)
    take_screenshot(page, "auth/AUTH-SEC-001-before.png")
    
    # Step 2: Verify redirect to profile page (actual redirect after patient login)
    assert "/accounts/profile/" in page.url or "/profile/" in page.url
    
    # Step 3: Attempt to navigate to /appointments/admin/dashboard/
    page.goto(f"{BASE_URL}/appointments/admin/dashboard/")
    page.wait_for_load_state("networkidle")
    
    # Step 4: Verify redirect to profile page (access denied by redirect)
    # The application redirects unauthorized users back to their profile page
    page.wait_for_url(re.compile(r".*\/accounts\/profile\/.*"), timeout=30000)
    assert "/accounts/profile/" in page.url, f"Expected redirect to /accounts/profile/ but got {page.url}"
    
    # Step 5: Attempt to navigate to /owner/
    page.goto(f"{BASE_URL}/owner/")
    page.wait_for_load_state("networkidle")
    
    # Step 6: Verify redirect to profile page (access denied by redirect)
    # The application redirects unauthorized users back to their profile page
    page.wait_for_url(re.compile(r".*\/accounts\/profile\/.*"), timeout=30000)
    assert "/accounts/profile/" in page.url, f"Expected redirect to /accounts/profile/ but got {page.url}"
    
    # Screenshot after
    take_screenshot(page, "auth/AUTH-SEC-001-after.png")

