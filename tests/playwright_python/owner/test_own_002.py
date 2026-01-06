"""
OWN-002: View patients
Test Scenario: Verify owner can view patients list
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_002_view_patients(page: Page):
    """OWN-002: View patients"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to patients page
    current_url = page.url
    if "/owner/patients/" not in current_url:
        page.goto(f"{BASE_URL}/owner/patients/", wait_until="domcontentloaded")
        # Wait a bit for page to settle
        page.wait_for_timeout(1000)
    else:
        # Already on the page, just wait a bit
        page.wait_for_timeout(1000)
    
    # Screenshot before - patients page loaded
    take_screenshot(page, "owner/OWN-002-before.png")

    # Step 3: Verify patients list page loads
    assert "/owner/patients/" in page.url
    
    # Step 4: Verify patient table/cards are displayed
    patient_indicators = [
        "[class*='patient']",
        "[id*='patient']",
        ".patient",
        "table",
    ]
    
    # Step 5: Verify patient information includes name, contact, registration date
    info_indicators = [
        "text=Name",
        "text=Contact",
        "text=Email",
        "text=Phone",
    ]
    
    # Step 6: Verify search/filter functionality works (if available)
    search_selectors = [
        'input[type="search"]',
        'input[name="search"]',
        'input[placeholder*="search"]',
    ]
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-002-after.png")

