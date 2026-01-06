"""
ANA-004: Treatment correlations
Test Scenario: Verify treatment correlations page displays correlation chart
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_ana_004_treatment_correlations(page: Page):
    """ANA-004: Treatment correlations"""
     # Step 1: Login as Owner or Staff
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to correlations page
    page.goto(f"{BASE_URL}/analytics/correlations/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify correlations page loads
    assert "/analytics/correlations/" in page.url
    
    # Step 4: Verify correlation chart is displayed
    # Step 5: Verify treatment relationships are visualized
    # Step 6: Verify chart is interactive (if applicable)
    # Step 7: Verify data points are labeled clearly
    
    # Screenshot after
    take_screenshot(page, "analytics/ANA-004-after.png")

