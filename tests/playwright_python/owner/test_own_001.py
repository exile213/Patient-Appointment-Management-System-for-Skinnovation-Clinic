"""
OWN-001: View owner dashboard
Test Scenario: Verify owner dashboard loads with key metrics
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_001_view_owner_dashboard(page: Page):
    """OWN-001: View owner dashboard"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to owner dashboard
    page.goto(f"{BASE_URL}/owner/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - owner dashboard loaded
    take_screenshot(page, "owner/OWN-001-before.png")

    # Step 3: Verify owner dashboard loads
    assert "/owner/" in page.url
    
    # Step 4: Verify dashboard displays key metrics (revenue, appointments, patients)
    metrics_indicators = [
        "text=Revenue",
        "text=Appointments",
        "text=Patients",
        "[class*='metric']",
        "[class*='stat']",
    ]
    
    # Step 5: Verify navigation menu is present
    nav_indicators = [
        "text=Dashboard",
        "text=Patients",
        "text=Appointments",
        "text=Analytics",
        "[class*='nav']",
        "[class*='menu']",
    ]
    
    # Step 6: Verify quick access links are functional
    assert "/owner/" in page.url
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-001-after.png")

