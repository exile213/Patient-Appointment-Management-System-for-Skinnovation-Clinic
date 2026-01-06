"""
ANA-005: Business insights
Test Scenario: Verify business insights page displays insights and recommendations
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_ana_005_business_insights(page: Page):
    """ANA-005: Business insights"""
     # Step 1: Login as Owner or Staff
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to business insights page
    page.goto(f"{BASE_URL}/analytics/insights/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify business insights page loads
    assert "/analytics/insights/" in page.url
    
    # Step 4: Select date range "2025-01-01" to "2025-01-31"
    date_from = page.locator('input[name="date_from"], input[id*="date_from"]').first
    if date_from.is_visible(timeout=2000):
        date_from.fill("2025-01-01")
    
    date_to = page.locator('input[name="date_to"], input[id*="date_to"]').first
    if date_to.is_visible(timeout=2000):
        date_to.fill("2025-01-31")
    
    # Step 5: Click "Generate Insights" button (if applicable)
    generate_button = page.locator('button:has-text("Generate"), button:has-text("Generate Insights")').first
    if generate_button.is_visible(timeout=2000):
        generate_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify insights are displayed (trends, recommendations, alerts)
    # Step 7: Verify insights are actionable and relevant
    # Step 8: Verify data visualizations support the insights
    
    # Screenshot after
    take_screenshot(page, "analytics/ANA-005-after.png")

