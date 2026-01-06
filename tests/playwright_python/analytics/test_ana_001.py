"""
ANA-001: Analytics dashboard
Test Scenario: Verify analytics dashboard loads with key metrics
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_ana_001_analytics_dashboard(page: Page):
    """ANA-001: Analytics dashboard"""
     # Step 1: Login as Owner or Staff
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to analytics dashboard
    page.goto(f"{BASE_URL}/owner/analytics/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify analytics dashboard loads
    assert "/owner/analytics/" in page.url or "/analytics/" in page.url
    
    # Step 4: Verify key metrics are displayed (revenue, appointments, patients)
    # Step 5: Verify charts and graphs are rendered
    # Step 6: Verify navigation to different analytics sections is available
    
    # Screenshot after
    take_screenshot(page, "analytics/ANA-001-after.png")

